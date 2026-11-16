"""Exporta a JSON lo que muestra la web (carpeta web/).

La web es estatica: no consulta la base, lee archivos JSON. Este script los
escribe en web/public/datos/ a partir de la base y de los mismos calculos que
usa el resto del proyecto (src/indicators). Correr despues de integrar.py:

    python scripts/exportar_web.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.rutas import BASE_DUCKDB, RAIZ
from src.indicators import vigilancia, volatilidad

SALIDA = RAIZ / "web" / "public" / "datos"
MESES_DE_HISTORIA = 24      # cuantos meses hacia atras lleva cada serie
NACIONAL = "Nacional"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def nombre_mes(periodo: int) -> str:
    """202609 -> 'septiembre de 2026'."""
    return f"{MESES[periodo % 100 - 1]} de {periodo // 100}"


def nombre_producto(producto: str) -> str:
    """Quita el asterisco con que el DANE marca algunos productos."""
    return producto.replace("*", "").strip()


def nombre_mercado(mercado: str) -> str:
    """'SAN JOSÉ DE CÚCUTA' -> 'San José de Cúcuta'."""
    return mercado.title().replace(" De ", " de ").replace("D.c.", "D.C.")


def _sumar_meses(periodo: int, meses: int) -> int:
    n = periodo // 100 * 12 + periodo % 100 - 1 + meses
    return n // 12 * 100 + n % 12 + 1


def _numero(valor, decimales: int = 1):
    """Numero redondeado, o None si no hay dato (JSON no admite NaN)."""
    return None if pd.isna(valor) else round(float(valor), decimales)


def _estado(alerta) -> str:
    """El semaforo como texto; un mes sin historia suficiente es 'sin dato', no verde."""
    return "sin dato" if pd.isna(alerta) else str(alerta)


def precios_con_nacional(precios: pd.DataFrame) -> pd.DataFrame:
    """Los precios por mercado mas una serie 'Nacional' (la mediana de los mercados).

    Solo meses cerrados: el mes en curso tiene pocos dias y su promedio cambia.
    """
    cerrados = precios[precios["mes_cerrado"]]
    nacional = vigilancia.retornos_nacionales(precios)[["producto", "periodo", "precio_cop_kg"]]
    return pd.concat([cerrados[["mercado", "producto", "periodo", "precio_cop_kg"]],
                      nacional.assign(mercado=NACIONAL)], ignore_index=True)


def armar_tablero(precios: pd.DataFrame, pronosticos: pd.DataFrame) -> dict:
    """Una fila por producto y mercado con todo lo que pinta el tablero.

    precios:     col_precio_mayorista_mensual
    pronosticos: resultado_pronostico_precio (solo existe para el precio nacional)
    """
    todos = precios_con_nacional(precios)
    # Los dos semaforos: frente al mes pasado y frente al mismo mes del anio pasado.
    calculado = volatilidad.comparacion_anual(volatilidad.alertas(todos))
    ultimo = int(calculado["periodo"].max())
    ventana = [_sumar_meses(ultimo, -k) for k in range(MESES_DE_HISTORIA - 1, -1, -1)]

    futuros = pronosticos[pronosticos["tipo"] == "pronostico"].sort_values("horizonte")
    filas = []
    for (mercado, producto), serie in calculado.groupby(["mercado", "producto"]):
        hoy = serie[serie["periodo"] == ultimo]
        if hoy.empty:          # ese mercado no tuvo precio el ultimo mes: no hay nada que comparar
            continue
        hoy = hoy.iloc[0]
        por_periodo = serie.set_index("periodo")["precio_cop_kg"]
        fila = {
            "producto": nombre_producto(producto),
            "mercado": NACIONAL if mercado == NACIONAL else nombre_mercado(mercado),
            "precio": _numero(hoy["precio_cop_kg"], 0),
            "cambio_mes_pct": _numero((np.exp(hoy["retorno_log"]) - 1) * 100),
            "estado_mes": _estado(hoy["alerta"]),
            "z_mes": _numero(hoy["z_score"], 2),
            "cambio_anio_pct": _numero(hoy["cambio_anual_pct"]),
            "estado_anio": _estado(hoy["alerta_anual"]),
            "z_anio": _numero(hoy["z_anual"], 2),
            # Un mes sin precio va como null: en la grafica se ve el hueco, no una linea inventada.
            "serie": [_numero(por_periodo.get(p), 0) for p in ventana],
            "pronostico": None,
        }
        if mercado == NACIONAL:
            futuro = futuros[futuros["producto"] == producto]
            if not futuro.empty:
                a_un_mes = futuro.iloc[0]
                fila["pronostico"] = {
                    "meses": [{"periodo": int(f.periodo), "valor": _numero(f.valor, 0),
                               "minimo": _numero(f.lim_inf, 0), "maximo": _numero(f.lim_sup, 0),
                               "metodo": f.modelo, "confiable": bool(f.gana_al_ingenuo)}
                              for f in futuro.itertuples()],
                    # La confianza es la del pronostico a un mes: se gana solo si el modelo
                    # se equivoca menos que suponer que el precio sigue igual.
                    "confiable": bool(a_un_mes["gana_al_ingenuo"]),
                    "error_modelo_pct": _numero(a_un_mes["mae_modelo"]),
                    "error_ingenuo_pct": _numero(a_un_mes["mae_ingenuo"]),
                }
        filas.append(fila)

    mercados = sorted({f["mercado"] for f in filas} - {NACIONAL})
    return {
        "ultimo_mes": ultimo,
        "ultimo_mes_texto": nombre_mes(ultimo),
        "generado": date.today().isoformat(),
        "periodos": ventana,
        "mercados": [NACIONAL] + mercados,
        "umbrales": {"amarilla": volatilidad.UMBRAL_AMARILLA, "roja": volatilidad.UMBRAL_ROJA},
        "filas": filas,
    }


# --- Mapa y clima ---------------------------------------------------------------------

MESES_DEL_MAPA = 12
GEOJSON = RAIZ / "config" / "geo" / "colombia_departamentos.geojson"

# Los nombres de config/departamentos.csv van sin tildes (son llaves de cruce).
# En pantalla se muestran bien escritos.
TILDES = {"Atlantico": "Atlántico", "Bogota": "Bogotá", "Bolivar": "Bolívar", "Boyaca": "Boyacá",
          "Caqueta": "Caquetá", "Cordoba": "Córdoba", "Choco": "Chocó", "Narino": "Nariño",
          "Quindio": "Quindío", "San Andres": "San Andrés", "Guainia": "Guainía", "Vaupes": "Vaupés"}


def simplificar(geojson: dict, decimales: int = 2) -> dict:
    """Redondea las coordenadas (2 decimales ~ 1 km) y quita los puntos repetidos.

    El archivo original pesa 1,5 MB porque trae detalle de metros; para pintar el
    pais en una pantalla sobra, y la web cargaria lento.
    """
    def anillo(puntos):
        salida = []
        for lon, lat in puntos:
            punto = [round(lon, decimales), round(lat, decimales)]
            if not salida or salida[-1] != punto:
                salida.append(punto)
        return salida if len(salida) >= 4 else None      # un anillo necesita al menos 4 puntos

    def poligono(anillos):
        limpios = [a for a in (anillo(r) for r in anillos) if a]
        return limpios or None

    rasgos = []
    for rasgo in geojson["features"]:
        geometria = rasgo["geometry"]
        partes = [geometria["coordinates"]] if geometria["type"] == "Polygon" else geometria["coordinates"]
        poligonos = [q for q in (poligono(parte) for parte in partes) if q]
        rasgos.append({"type": "Feature",
                       "properties": {"codigo": rasgo["properties"]["DPTO"]},
                       "geometry": {"type": "MultiPolygon", "coordinates": poligonos}})
    return {"type": "FeatureCollection", "features": rasgos}


def _serie_por_mes(tabla: pd.DataFrame, columna: str, periodos: list[int], decimales: int = 1) -> list:
    por_periodo = tabla.set_index("periodo")[columna]
    return [_numero(por_periodo.get(p), decimales) for p in periodos]


def armar_mapa(con: duckdb.DuckDBPyConnection, precios: pd.DataFrame) -> dict:
    """Lo que pinta el mapa: por departamento y mes, como va el precio y como va la lluvia."""
    departamentos = pd.read_csv(RAIZ / "config" / "departamentos.csv", dtype=str)
    mercados = con.execute("SELECT mercado, dpto_codigo FROM catalogo_mercado").df()

    # Precio: cambio frente al mismo mes del anio pasado, mediana de los productos del departamento.
    por_mercado = volatilidad.comparacion_anual(
        precios.loc[precios["mes_cerrado"], ["mercado", "producto", "periodo", "precio_cop_kg"]])
    ultimo = int(por_mercado["periodo"].max())
    periodos = [_sumar_meses(ultimo, -k) for k in range(MESES_DEL_MAPA - 1, -1, -1)]
    precio = (por_mercado.merge(mercados, on="mercado")
              .groupby(["dpto_codigo", "periodo"], as_index=False)
              .agg(cambio=("cambio_anual_pct", "median"), productos=("cambio_anual_pct", "count")))

    # Lluvia: lo que midieron los sensores del IDEAM frente a lo normal de ese mes, en %.
    sensor = con.execute(
        "SELECT departamento, periodo, valor, anomalia, n_estaciones FROM col_sensor_ideam_mensual "
        "WHERE variable = 'precipitacion'").df().merge(departamentos, on="departamento")
    normal = sensor["valor"] - sensor["anomalia"]
    sensor["lluvia_pct"] = (100 * sensor["anomalia"] / normal).where(normal > 0)

    estaciones = con.execute(
        "SELECT departamento, lat, lon FROM col_estacion_ideam WHERE lat IS NOT NULL").df().merge(
        departamentos, on="departamento")
    por_venir = con.execute("SELECT * FROM mundo_pronostico_lluvia ORDER BY departamento, periodo").df()

    filas = []
    for d in departamentos.itertuples():
        p = precio[precio["dpto_codigo"] == d.dpto_codigo]
        s = sensor[sensor["dpto_codigo"] == d.dpto_codigo]
        futuro = por_venir[por_venir["dpto_codigo"] == d.dpto_codigo]
        filas.append({
            "codigo": d.dpto_codigo,
            "nombre": TILDES.get(d.departamento, d.departamento),
            "precio": _serie_por_mes(p, "cambio", periodos) if not p.empty else None,
            "lluvia": _serie_por_mes(s, "lluvia_pct", periodos, 0) if not s.empty else None,
            "lluvia_mm": _serie_por_mes(s, "valor", periodos, 0) if not s.empty else None,
            "estaciones": int((estaciones["dpto_codigo"] == d.dpto_codigo).sum()),
            # No se exporta anomalia_p50: resta el pronostico (un modelo) contra lo observado
            # (otro modelo), y esa diferencia mide mas el desajuste entre modelos que la lluvia.
            # Medido el 2026-11-15: da -317 mm para Tolima, donde ni llueve tanto.
            "lluvia_esperada": [{"periodo": int(f.periodo), "seco": _numero(f.precip_p10, 0),
                                 "central": _numero(f.precip_p50, 0), "lluvioso": _numero(f.precip_p90, 0)}
                                for f in futuro.itertuples()] or None,
        })

    nino = con.execute("SELECT anio * 100 + mes AS periodo, trimestre, anomalia, fase, provisional "
                       "FROM mundo_fenomeno_nino ORDER BY periodo DESC LIMIT 36").df().iloc[::-1]
    hoy = nino.iloc[-1]
    return {
        "periodos": periodos,
        "departamentos": filas,
        # Cada estacion es un punto [longitud, latitud]: son los sensores reales del IDEAM.
        "estaciones": [[round(float(e.lon), 3), round(float(e.lat), 3)] for e in estaciones.itertuples()],
        "nino": {"fase": hoy["fase"], "anomalia": _numero(hoy["anomalia"], 2), "periodo": int(hoy["periodo"]),
                 "trimestre": hoy["trimestre"], "provisional": bool(hoy["provisional"]),
                 "serie": [{"periodo": int(f.periodo), "anomalia": _numero(f.anomalia, 2)}
                           for f in nino.itertuples()]},
    }


# --- El clima mueve los precios? ------------------------------------------------------

# Los cuatro eslabones de la cadena, en el orden en que se cuentan en pantalla.
ESLABONES = [
    ("oni->lluvia", "El Niño", "Lluvia", "¿El Niño cambia la lluvia?"),
    ("lluvia->oferta", "Lluvia", "Comida que llega", "¿La lluvia cambia cuánta comida llega?"),
    ("oferta->precio", "Comida que llega", "Precio", "¿Si llega menos comida, sube el precio?"),
    ("lluvia->precio", "Lluvia", "Precio", "De un salto: ¿la lluvia cambia el precio?"),
]
Q_FIRME = 0.1      # la regla del proyecto: una relacion se sostiene si su q-valor es menor


def armar_clima(con: duckdb.DuckDBPyConnection, precios: pd.DataFrame) -> dict:
    """Que tanto se sostiene cada eslabon entre el clima y el precio, y las pistas del mes."""
    efecto = con.execute("SELECT * FROM resultado_efecto_clima").df()
    cadena = []
    for clave, desde, hasta, pregunta in ESLABONES:
        pruebas = efecto[efecto["eslabon"] == clave]
        firmes = pruebas[pruebas["q_valor"] < Q_FIRME]
        # De cada producto o zona se muestra solo su relacion mas clara, no todos sus rezagos.
        llave = "departamento" if clave == "oni->lluvia" else "producto"
        mejores = firmes.sort_values("q_valor").drop_duplicates(llave).head(6)
        cadena.append({
            "eslabon": clave, "desde": desde, "hasta": hasta, "pregunta": pregunta,
            "pruebas": int(len(pruebas)), "firmes": int(len(firmes)),
            "hallazgos": [{"producto": None if pd.isna(h.producto) else nombre_producto(h.producto),
                           "departamento": None if pd.isna(h.departamento) else TILDES.get(h.departamento, h.departamento),
                           "rezago_meses": int(h.rezago_meses), "coeficiente": _numero(h.coeficiente, 3)}
                          for h in mejores.itertuples()],
        })

    # Pistas para el mes que viene: relaciones fuertes entre la lluvia pasada y el precio.
    ret = vigilancia.retornos_nacionales(precios)
    clima = con.execute("SELECT * FROM mundo_clima_zona_mensual").df()
    zonas = con.execute("SELECT * FROM catalogo_zona_productora WHERE producto_sipsa IS NOT NULL").df()
    correlaciones = vigilancia.correlacion_lluvia(ret, clima, zonas)
    ultimo = int(precios.loc[precios["mes_cerrado"], "periodo"].max())
    proximo = _sumar_meses(ultimo, 1)
    senales = vigilancia.senales(correlaciones, clima, zonas, proximo)
    aciertos = vigilancia.acierto_historico(ret, clima, zonas, correlaciones)
    pistas = []
    for s in senales.merge(aciertos, on=["producto", "departamento", "rezago"]).itertuples():
        pistas.append({
            "producto": nombre_producto(s.producto),
            "departamento": TILDES.get(s.departamento, s.departamento),
            "rezago_meses": int(s.rezago), "mes_de_la_lluvia": int(s.periodo_lluvia),
            "llovio_mas": None if pd.isna(s.anomalia) else bool(s.anomalia > 0),
            "senal": s.senal,                                  # "al alza", "a la baja" o "sin dato"
            "aciertos": int(s.aciertos), "meses": int(s.meses),
        })

    quiebres = con.execute("SELECT count(*), count(*) FILTER (WHERE hay_quiebre) FROM resultado_quiebres").fetchone()
    return {"cadena": cadena, "pistas": pistas, "proximo_mes": proximo,
            "quiebres": {"pruebas": int(quiebres[0]), "firmes": int(quiebres[1])}}


# --- Fuentes y huecos -----------------------------------------------------------------

# De donde sale cada dato. `ultimo` es la consulta que dice hasta cuando llega.
FUENTES = [
    {"nombre": "SIPSA · precios mayoristas", "entidad": "DANE", "origen": "nacional",
     "aporta": "El precio de cada alimento en cada central mayorista. Es el dato central del proyecto.",
     "frecuencia": "Diaria", "tablas": ["col_precio_mayorista_mensual", "col_precio_mayorista_semanal"],
     "ultimo": "SELECT strftime(max(semana_inicio), '%Y-%m-%d') FROM col_precio_mayorista_semanal"},
    {"nombre": "SIPSA · abastecimiento", "entidad": "DANE", "origen": "nacional",
     "aporta": "Las toneladas de cada alimento que entran a cada central: la oferta.",
     "frecuencia": "Mensual", "tablas": ["col_abastecimiento_mensual"],
     "ultimo": "SELECT max(periodo) FROM col_abastecimiento_mensual"},
    {"nombre": "Sensores automáticos", "entidad": "IDEAM", "origen": "nacional",
     "aporta": "Lluvia y temperatura medidas en tierra por estaciones del país. Es la fuente de sensor.",
     "frecuencia": "Cada 10 minutos a 1 hora", "tablas": ["col_sensor_ideam_mensual", "col_estacion_ideam"],
     "ultimo": "SELECT max(periodo) FROM col_sensor_ideam_mensual"},
    {"nombre": "FAOSTAT", "entidad": "FAO (Naciones Unidas)", "origen": "internacional",
     "aporta": "Precio al productor, producción, comercio, balance alimentario y valor de la producción de Colombia.",
     "frecuencia": "Anual, con uno o dos años de rezago", "tablas": ["mundo_fao_colombia"],
     "ultimo": "SELECT max(anio) FROM mundo_fao_colombia"},
    {"nombre": "NASA POWER", "entidad": "NASA", "origen": "internacional",
     "aporta": "Lluvia y temperatura estimadas por satélite en las zonas donde se cultiva cada producto, desde 1991.",
     "frecuencia": "Mensual", "tablas": ["mundo_clima_zona_mensual"],
     "ultimo": "SELECT max(periodo) FROM mundo_clima_zona_mensual"},
    {"nombre": "Índice ONI", "entidad": "NOAA (Estados Unidos)", "origen": "internacional",
     "aporta": "Si hay fenómeno de El Niño o de La Niña, y qué tan fuerte.",
     "frecuencia": "Mensual", "tablas": ["mundo_fenomeno_nino"],
     "ultimo": "SELECT max(anio * 100 + mes) FROM mundo_fenomeno_nino"},
    {"nombre": "Open-Meteo", "entidad": "Open-Meteo", "origen": "internacional",
     "aporta": "Clima de cada día y el pronóstico: 16 días y los próximos meses.",
     "frecuencia": "Diaria", "tablas": ["mundo_clima_diario", "mundo_pronostico_lluvia"],
     "ultimo": "SELECT strftime(max(fecha), '%Y-%m-%d') FROM mundo_clima_diario WHERE tipo = 'observado'"},
    {"nombre": "Pink Sheet", "entidad": "Banco Mundial", "origen": "internacional",
     "aporta": "El precio internacional de los fertilizantes, el principal insumo de los cultivos.",
     "frecuencia": "Mensual", "tablas": ["mundo_precio_fertilizantes"],
     "ultimo": "SELECT max(periodo) FROM mundo_precio_fertilizantes"},
]


def _fecha_legible(valor) -> str:
    """202609 -> 'septiembre de 2026'; 2024 -> '2024'; '2026-10-03' -> '3 de octubre de 2026'."""
    texto = str(valor)
    if len(texto) == 6 and texto.isdigit():
        return nombre_mes(int(texto))
    if len(texto) == 10:
        anio, mes, dia = (int(x) for x in texto.split("-"))
        return f"{dia} de {MESES[mes - 1]} de {anio}"
    return texto


def armar_fuentes(con: duckdb.DuckDBPyConnection) -> dict:
    """Las fuentes, separadas en nacionales e internacionales, y lo que todavia falta."""
    uno = lambda sql: con.execute(sql).fetchone()[0]
    fuentes = [{
        **{k: f[k] for k in ("nombre", "entidad", "origen", "aporta", "frecuencia", "tablas")},
        "filas": sum(uno(f'SELECT count(*) FROM "{t}"') for t in f["tablas"]),
        "ultimo_dato": _fecha_legible(uno(f["ultimo"])),
    } for f in FUENTES]

    # Los huecos se miden, no se suponen: cada cifra sale de una consulta.
    total_deptos = len(pd.read_csv(RAIZ / "config" / "departamentos.csv"))
    meses = con.execute("SELECT DISTINCT periodo FROM col_precio_mayorista_mensual ORDER BY 1").df()["periodo"]
    esperados = (meses.max() // 100 - meses.min() // 100) * 12 + (meses.max() % 100 - meses.min() % 100) + 1
    productos = uno("SELECT count(*) FROM catalogo_producto")
    huecos = {
        "departamentos": total_deptos,
        "departamentos_con_precio": uno("SELECT count(DISTINCT dpto_codigo) FROM catalogo_mercado"),
        "departamentos_con_sensor": uno("SELECT count(DISTINCT departamento) FROM col_sensor_ideam_mensual"),
        "meses_sin_precio": int(esperados - len(meses)),
        "productos": productos,
        "productos_con_zona": uno("SELECT count(DISTINCT producto_sipsa) FROM catalogo_zona_productora "
                                  "WHERE producto_sipsa IS NOT NULL"),
        "productos_comparables_fao": uno("SELECT count(*) FROM catalogo_producto WHERE permite_comparar_precio"),
        "pronosticos_confiables": uno("SELECT count(*) FROM resultado_pronostico_precio "
                                      "WHERE tipo = 'pronostico' AND horizonte = 1 AND gana_al_ingenuo"),
        "relaciones_clima": uno("SELECT count(*) FROM resultado_efecto_clima"),
        "relaciones_clima_firmes": uno("SELECT count(*) FROM resultado_efecto_clima WHERE q_valor < 0.1"),
        "ultimo_precio": nombre_mes(int(uno("SELECT max(periodo) FROM col_precio_mayorista_mensual WHERE mes_cerrado"))),
        "ultimo_abastecimiento": nombre_mes(int(uno("SELECT max(periodo) FROM col_abastecimiento_mensual"))),
    }
    return {"fuentes": fuentes, "huecos": huecos}


def _escribir(nombre: str, contenido: dict) -> None:
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / nombre
    destino.write_text(json.dumps(contenido, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"  {destino.relative_to(RAIZ)}: {destino.stat().st_size / 1024:.0f} KB")


def main() -> int:
    con = duckdb.connect(str(BASE_DUCKDB), read_only=True)
    precios = con.execute("SELECT * FROM col_precio_mayorista_mensual").df()
    pronosticos = con.execute("SELECT * FROM resultado_pronostico_precio").df()

    _escribir("tablero.json", armar_tablero(precios, pronosticos))
    _escribir("mapa.json", armar_mapa(con, precios))
    _escribir("clima.json", armar_clima(con, precios))
    _escribir("fuentes.json", armar_fuentes(con))
    _escribir("colombia.json", simplificar(json.loads(GEOJSON.read_text(encoding="utf-8"))))
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
