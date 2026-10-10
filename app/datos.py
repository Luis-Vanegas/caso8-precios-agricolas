"""Acceso a datos para la app. Unico lugar que abre la base.

Todo va con cache: DuckDB es rapido, pero Streamlit reejecuta el script entero
en cada interaccion y sin cache se releeria la base en cada clic.

La base se abre en solo lectura. La app nunca escribe.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.rutas import BASE_DUCKDB, CONFIG

TTL = 3600  # segundos


@st.cache_resource
def conexion() -> duckdb.DuckDBPyConnection:
    """Conexion de solo lectura, compartida por toda la sesion."""
    if not BASE_DUCKDB.exists():
        st.error(
            f"No existe {BASE_DUCKDB.name}. Correr `python scripts/integrar.py` "
            "despues de `carga_inicial.py` y `preparar.py`."
        )
        st.stop()
    try:
        return duckdb.connect(str(BASE_DUCKDB), read_only=True)
    except duckdb.IOException:
        # En Windows, si otro script tiene la base abierta para escribir
        # (actualizar.py o integrar.py), nadie mas la puede abrir.
        st.warning(
            "La base de datos se está actualizando en este momento. "
            "Esperá a que termine `actualizar.py` o `integrar.py` y recargá la página."
        )
        st.stop()


@st.cache_data(ttl=TTL)
def consultar(sql: str) -> pd.DataFrame:
    """Ejecuta una consulta y devuelve un DataFrame cacheado."""
    return conexion().execute(sql).df()


@st.cache_data(ttl=TTL)
def precios_mayoristas() -> pd.DataFrame:
    return consultar("SELECT * FROM fact_precio_mayorista")


@st.cache_data(ttl=TTL)
def con_indicadores() -> pd.DataFrame:
    """Precios mayoristas con retorno, volatilidad y semaforo ya calculados."""
    from src.indicators.volatilidad import alertas

    return alertas(precios_mayoristas())


@st.cache_data(ttl=TTL)
def frescura() -> pd.DataFrame:
    """Ultima descarga por fuente. Alimenta el panel de frescura."""
    return consultar(
        """
        SELECT fuente, ultimo_periodo, fecha_descarga,
               fecha_actualizacion_fuente, estado, filas, mensaje
        FROM meta_actualizacion
        QUALIFY ROW_NUMBER() OVER (PARTITION BY fuente ORDER BY fecha_descarga DESC) = 1
        ORDER BY fuente
        """
    )


@st.cache_data(ttl=TTL)
def puente() -> pd.DataFrame:
    return consultar("SELECT * FROM puente_producto ORDER BY producto_sipsa")


@st.cache_data(ttl=TTL)
def enso() -> pd.DataFrame:
    return consultar("SELECT * FROM fact_enso ORDER BY anio, mes")


@st.cache_data(ttl=TTL)
def clima() -> pd.DataFrame:
    return consultar("SELECT * FROM fact_clima ORDER BY anio, mes")


def aviso_cache() -> None:
    """Nota fija: la app siempre lee de DuckDB, nunca llama a las APIs en vivo.

    Es una decision de diseño, no una limitacion: si una fuente esta caida, la
    app sigue funcionando y el panel de frescura dice cuan viejo es el dato.
    """
    st.caption(
        "La app lee del archivo DuckDB versionado, no de las APIs en vivo. "
        "El panel de frescura indica la antigüedad de cada fuente."
    )


# --- Ayudas para las paginas rediseñadas ------------------------------------


def fecha(periodo: int) -> str:
    """202608 -> 'ago 2026'. Mas facil de leer que el numero."""
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{meses[periodo % 100 - 1]} {periodo // 100}"


@st.cache_data(ttl=TTL)
def ultimo_mes_cerrado() -> int:
    """Ultimo periodo AAAAMM cuyo mes ya termino.

    El mes en curso tiene pocos dias de dato y su promedio todavia cambia, asi
    que la portada muestra el ultimo mes completo. Si la base es anterior a la
    columna `mes_cerrado`, usa el ultimo periodo disponible.
    """
    columnas = consultar("DESCRIBE fact_precio_mayorista")["column_name"].tolist()
    filtro = "WHERE mes_cerrado" if "mes_cerrado" in columnas else ""
    return int(consultar(f"SELECT max(periodo) AS p FROM fact_precio_mayorista {filtro}")["p"][0])


SEVERIDAD = {"verde": 0, "amarilla": 1, "roja": 2}
GLIFO = {0: "", 1: "●", 2: "▲"}


@st.cache_data(ttl=TTL)
def matriz_canasta(desde: int, hasta: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list[str]]:
    """Matriz producto x periodo con el estado del semaforo de cada mes.

    Un producto se vende en varios mercados y cada mercado tiene su propia
    alerta. La celda muestra la *peor* alerta del mes: un semaforo avisa por el
    caso mas grave, no por el promedio. No se promedian precios de mercados
    distintos (lo prohibe docs/contrato_datos.md).

    Devuelve (severidad, glifos, detalle, etiquetas):
    - severidad: 0 verde, 1 amarilla, 2 roja, vacio si el mes no tiene dato
    - glifos:    el signo que acompana al color (el color nunca va solo)
    - detalle:   texto del tooltip
    - etiquetas: los meses ya legibles ('ago 2026')

    Los meses del hueco de SIPSA (2021-01 a 2022-01) se incluyen vacios para que
    el hueco se vea como hueco y no se lea como "sin alertas".
    """
    df = con_indicadores()
    df = df[(df["periodo"] >= desde) & (df["periodo"] <= hasta)]
    # `alerta` es Categorical: hay que pasar por str antes de mapear (regla de CLAUDE.md).
    df = df.assign(severidad=df["alerta"].astype(str).map(SEVERIDAD))
    df = df.dropna(subset=["severidad"])

    peor = df.groupby(["producto", "periodo"])["severidad"].max().unstack("periodo")
    encendidas = df[df["severidad"] > 0]
    cuantas = encendidas.groupby(["producto", "periodo"]).size().unstack("periodo")
    total = df.groupby(["producto", "periodo"]).size().unstack("periodo")

    # Todos los meses del rango, incluso los que ninguna serie reporta.
    meses = [p for a in range(desde // 100, hasta // 100 + 1)
             for m in range(1, 13) if desde <= (p := a * 100 + m) <= hasta]
    peor = peor.reindex(columns=meses)

    # Los productos con mas meses en alerta van arriba: el hallazgo primero.
    orden = (peor > 0).sum(axis=1).sort_values(ascending=False).index
    peor = peor.loc[orden]
    # `cuantas` solo trae los productos que se encendieron alguna vez, asi que se
    # reindexa contra la matriz completa (si no, falta un producto y revienta).
    cuantas = cuantas.reindex(index=orden, columns=meses)
    total = total.reindex(index=orden, columns=meses)

    peor.index = peor.index.str.replace("*", "", regex=False)
    glifos = peor.map(lambda v: GLIFO.get(v, "") if pd.notna(v) else "")
    nombre = {0: "sin alerta", 1: "alerta amarilla", 2: "alerta roja"}
    detalle = pd.DataFrame(
        [[_detalle(peor.iat[i, j], cuantas.iat[i, j], total.iat[i, j], nombre)
          for j in range(peor.shape[1])] for i in range(peor.shape[0])],
        index=peor.index, columns=peor.columns,
    )
    return peor, glifos, detalle, [fecha(p) for p in meses]


def _detalle(severidad, encendidas, mercados, nombre: dict) -> str:
    """Texto del tooltip de una celda."""
    if pd.isna(severidad):
        return "sin dato este mes"
    texto = nombre[int(severidad)]
    if severidad > 0 and pd.notna(encendidas):
        texto += f" en {int(encendidas)} de {int(mercados)} mercados"
    elif pd.notna(mercados):
        texto += f" en {int(mercados)} mercados"
    return texto


# --- Mapa por departamento ---------------------------------------------------
# El mapa colorea por VARIACION %, nunca por nivel de precio: la misma "papa" es
# otra variedad en cada ciudad, asi que comparar niveles entre departamentos
# compara cosas distintas (regla 4 de docs/contrato_datos.md).

# Un articulo que se vende en 2 departamentos o menos no va al mapa: con dos
# puntos no hay nada que leer geograficamente (regla 6 del contrato).
MINIMO_DEPARTAMENTOS = 3

# El mes anterior en el calendario. En enero hay que saltar a diciembre del anio
# pasado: 202601 - 89 = 202512. Nunca se usa la fila anterior de la tabla.
_MES_ANTERIOR = "CASE WHEN {p} % 100 = 1 THEN {p} - 89 ELSE {p} - 1 END"

_PRECIO_MENSUAL = """
    SELECT art_id, articulo, dpto_codigo, departamento, mercado, periodo,
           median(precio) AS precio, any_value(unidad) AS unidad
    FROM fact_precio_semanal
    GROUP BY art_id, articulo, dpto_codigo, departamento, mercado, periodo
"""


@st.cache_data(ttl=TTL)
def articulos_del_mapa() -> pd.DataFrame:
    """Articulos que aparecen en suficientes departamentos para dibujar un mapa."""
    return consultar(f"""
        SELECT art_id, any_value(articulo) AS articulo, any_value(unidad) AS unidad,
               count(DISTINCT dpto_codigo) AS departamentos
        FROM fact_precio_semanal
        GROUP BY art_id
        HAVING count(DISTINCT dpto_codigo) >= {MINIMO_DEPARTAMENTOS}
        ORDER BY articulo
    """)


# Un mes de SIPSA semanal trae 4 o 5 semanas. Con menos, el mes todavia no
# termino y su promedio no es comparable contra un mes completo.
SEMANAS_MES_COMPLETO = 4


@st.cache_data(ttl=TTL)
def periodos_semanal() -> pd.DataFrame:
    """Meses de los precios semanales, del mas nuevo al mas viejo, con `parcial`.

    Se excluye el mes mas viejo: sin el mes anterior no hay variacion que mostrar.
    """
    df = consultar("""
        SELECT periodo, count(DISTINCT semana_inicio) AS semanas
        FROM fact_precio_semanal
        GROUP BY periodo ORDER BY periodo
    """)
    df = df.iloc[1:].copy()
    df["parcial"] = df["semanas"] < SEMANAS_MES_COMPLETO
    return df.sort_values("periodo", ascending=False).reset_index(drop=True)


@st.cache_data(ttl=TTL)
def variacion_departamentos(art_id: int, periodo: int) -> pd.DataFrame:
    """Variacion % del precio de un articulo por departamento, contra el mes anterior.

    Un departamento puede tener varios mercados (Antioquia tiene 11). El valor
    del departamento es la **mediana de las variaciones %** de sus mercados, no
    el promedio de sus precios: promediar precios de mercados distintos esta
    prohibido por el contrato de datos.
    """
    anterior = _MES_ANTERIOR.format(p="a.periodo")
    return consultar(f"""
        WITH mensual AS ({_PRECIO_MENSUAL}),
        comparado AS (
            SELECT a.dpto_codigo, a.departamento, a.mercado, a.unidad,
                   (a.precio / b.precio - 1) * 100 AS variacion
            FROM mensual a
            JOIN mensual b
              ON a.art_id = b.art_id AND a.mercado = b.mercado AND b.periodo = {anterior}
            WHERE a.art_id = {int(art_id)} AND a.periodo = {int(periodo)}
        )
        SELECT dpto_codigo, departamento, any_value(unidad) AS unidad,
               count(*) AS mercados, median(variacion) AS variacion
        FROM comparado
        GROUP BY dpto_codigo, departamento
        ORDER BY variacion DESC
    """)


# --- Canasta familiar con el precio semanal ----------------------------------
# Los precios diarios solo traen 33 productos (frutas y verduras). La canasta
# familiar (arroz, huevo, pollo, carnes, aceite, panela, queso...) solo esta en
# el precio semanal, marcada con `en_canasta` en el catalogo.


def fecha_dia(dia) -> str:
    """Timestamp -> '11 oct 2025'. Para declarar el periodo cubierto."""
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{dia.day} {meses[dia.month - 1]} {dia.year}"


@st.cache_data(ttl=TTL)
def cobertura_canasta() -> pd.Series:
    """Primera y ultima semana, articulos y mercados de la canasta familiar.

    Se lee de la base y no se escribe a mano: la ventana del DANE se corre
    cada semana.
    """
    return consultar("""
        SELECT min(semana_inicio) AS desde, max(semana_inicio) AS hasta,
               count(DISTINCT art_id) AS articulos, count(DISTINCT mercado) AS mercados
        FROM fact_precio_semanal
        WHERE en_canasta
    """).iloc[0]


@st.cache_data(ttl=TTL)
def variacion_canasta() -> pd.DataFrame:
    """Variacion % mensual de cada articulo de la canasta familiar.

    Paso a paso, igual que el mapa:
    1. precio del mes de cada articulo en cada mercado (mediana de sus semanas);
    2. variacion % de ese mercado contra el mes anterior del calendario;
    3. la variacion del articulo es la mediana de las variaciones de sus mercados.
    Nunca se promedian precios de mercados distintos (docs/contrato_datos.md).
    """
    anterior = _MES_ANTERIOR.format(p="a.periodo")
    return consultar(f"""
        WITH mensual AS (
            SELECT art_id, mercado, periodo, median(precio) AS precio,
                   any_value(articulo) AS articulo, any_value(grupo_dane) AS grupo_dane,
                   any_value(unidad) AS unidad
            FROM fact_precio_semanal
            WHERE en_canasta
            GROUP BY art_id, mercado, periodo
        ), comparado AS (
            SELECT a.art_id, a.articulo, a.grupo_dane, a.unidad, a.periodo,
                   (a.precio / b.precio - 1) * 100 AS variacion
            FROM mensual a
            JOIN mensual b
              ON a.art_id = b.art_id AND a.mercado = b.mercado AND b.periodo = {anterior}
        )
        SELECT art_id, any_value(articulo) AS articulo, any_value(grupo_dane) AS grupo_dane,
               any_value(unidad) AS unidad, periodo,
               count(*) AS mercados, median(variacion) AS variacion
        FROM comparado
        GROUP BY art_id, periodo
        ORDER BY grupo_dane, articulo, periodo
    """)


# --- La cadena: lluvia -> toneladas -> precio --------------------------------


# El precio de la cadena puede salir de dos fuentes:
# - el precio SEMANAL: tiene el mismo art_id que el abastecimiento, pero solo
#   unos 13 meses (ventana movil del DANE);
# - el precio DIARIO (fact_precio_mayorista): desde 2020, pero con otros nombres.
#   Solo se usa cuando el nombre coincide exacto con el del abastecimiento
#   (`mapa_articulos` de src/indicators/sensibilidad.py, 24 productos). Asi no se
#   mezclan variedades: "Papa negra*" agrupa varias papas y no se empareja.


@st.cache_data(ttl=TTL)
def pares_diario() -> pd.DataFrame:
    """Articulo del abastecimiento -> producto del precio diario, solo nombres identicos."""
    from src.indicators.sensibilidad import mapa_articulos

    productos = consultar("SELECT DISTINCT producto FROM fact_precio_mayorista")["producto"]
    articulos = consultar("SELECT DISTINCT art_id, articulo FROM fact_abastecimiento")
    return mapa_articulos(productos, articulos)


def par_diario(art_id: int) -> str | None:
    """Nombre del producto del precio diario que es el mismo articulo, o None."""
    pares = pares_diario()
    fila = pares[pares["art_id"] == art_id]
    return None if fila.empty else str(fila["producto"].iloc[0])


@st.cache_data(ttl=TTL)
def mercados_diarios(dpto_codigo: str) -> list[str]:
    """Mercados del precio diario que quedan en ese departamento.

    config/mercados.csv dice el departamento de cada mercado por nombre, y
    config/departamentos.csv traduce el nombre a codigo DANE.
    """
    codigos = pd.read_csv(CONFIG / "departamentos.csv", dtype=str)
    mercados = mercados_geo().merge(codigos, on="departamento")
    return mercados.loc[mercados["dpto_codigo"] == dpto_codigo, "mercado"].tolist()


def fuente_precio(art_id: int, dpto_codigo: str) -> str | None:
    """Producto del precio diario a usar en la cadena, o None si va el semanal.

    Hacen falta las dos cosas: que el articulo tenga par exacto y que el
    departamento tenga un mercado del precio diario (Cundinamarca no tiene).
    """
    producto = par_diario(art_id)
    return producto if producto and mercados_diarios(dpto_codigo) else None


def _sql_texto(valor: str) -> str:
    """Comillas simples para SQL, escapando las de adentro."""
    return "'" + valor.replace("'", "''") + "'"


@st.cache_data(ttl=TTL)
def articulos_cadena() -> pd.DataFrame:
    """Articulos con abastecimiento y precio: los unicos con cadena completa.

    Se ordenan por cuantos meses de abastecimiento tienen tambien precio, no por
    toneladas: un articulo con mucho volumen pero sin meses en comun no tiene
    cadena que mostrar. Los que tienen par en el precio diario cuentan sus
    meses desde 2020; los demas, solo la ventana del semanal.
    """
    pares = pares_diario()
    valores = ", ".join(f"({int(f.art_id)}, {_sql_texto(f.producto)})"
                        for f in pares.itertuples()) or "(NULL, NULL)"
    return consultar(f"""
        WITH pares(art_id, producto) AS (VALUES {valores}),
        meses_con_precio AS (
            SELECT p.art_id, m.periodo
            FROM pares p
            JOIN (SELECT DISTINCT producto, periodo FROM fact_precio_mayorista) m USING (producto)
            UNION
            SELECT DISTINCT art_id, periodo FROM fact_precio_semanal
            WHERE art_id NOT IN (SELECT art_id FROM pares WHERE art_id IS NOT NULL)
        )
        SELECT a.art_id, any_value(a.articulo) AS articulo,
               count(DISTINCT m.periodo) AS meses_comparables,
               sum(a.toneladas) AS toneladas
        FROM fact_abastecimiento a
        LEFT JOIN meses_con_precio m ON a.art_id = m.art_id AND a.periodo = m.periodo
        WHERE a.art_id IN (SELECT art_id FROM meses_con_precio)
        GROUP BY a.art_id
        ORDER BY meses_comparables DESC, toneladas DESC
    """)


@st.cache_data(ttl=TTL)
def departamentos_cadena(art_id: int) -> pd.DataFrame:
    """Departamentos con clima y abastecimiento **de ese articulo**.

    El orden depende del articulo elegido: un departamento puede tener mucho
    abastecimiento en general y nada de este articulo. Primero los que tienen
    mas meses con las tres series a la vez (lluvia, toneladas y precio).
    """
    zonas = consultar(f"""
        SELECT DISTINCT a.departamento, a.dpto_codigo
        FROM fact_abastecimiento a
        WHERE a.art_id = {int(art_id)}
          AND a.dpto_codigo IN (SELECT DISTINCT dpto_codigo FROM fact_clima_diario)
    """)
    zonas["meses_comparables"] = [
        len(cadena(art_id, c, fuente_precio(art_id, c))
            .dropna(subset=["lluvia_mm", "toneladas", "precio"]))
        for c in zonas["dpto_codigo"]
    ]
    return zonas.sort_values(["meses_comparables", "departamento"],
                             ascending=[False, True]).reset_index(drop=True)


# Un hallazgo se declara con q < 0,10. El q-valor ya corrige por haber probado
# muchas parejas: con 140 pruebas, algunos p pequenos salen por azar.
UMBRAL_Q = 0.10


@st.cache_data(ttl=TTL)
def sensibilidad_cadena(art_id: int, departamento: str) -> pd.DataFrame:
    """Lo que midieron los indicadores para este articulo y departamento.

    Solo los eslabones que se pueden cruzar sin inventar correspondencias:
    `oferta->precio` y `lluvia->oferta` van por `art_id`, y `oni->lluvia` por
    departamento. El eslabon `lluvia->precio` se calculo sobre los nombres de
    los precios diarios, que usan otros codigos, asi que no se cruza por art_id.
    """
    if not tabla_existe("indicador_sensibilidad_clima"):
        return pd.DataFrame()
    dpto = departamento.replace("'", "''")
    return consultar(f"""
        SELECT eslabon, variable, rezago_meses, coeficiente, p_valor, q_valor, n, metodo
        FROM indicador_sensibilidad_clima
        WHERE (eslabon = 'oferta->precio' AND art_id = {int(art_id)})
           OR (eslabon = 'lluvia->oferta' AND art_id = {int(art_id)}
               AND departamento = '{dpto}')
           OR (eslabon = 'oni->lluvia' AND departamento = '{dpto}')
        ORDER BY q_valor
    """)


# --- ¿Cuanto afecta el clima? (indicador_sensibilidad_clima e indicador_quiebres) ---


@st.cache_data(ttl=TTL)
def sensibilidad_resumen() -> pd.DataFrame:
    """Una fila por eslabon: cuantas pruebas se hicieron y cuantas se sostienen.

    `hallazgos` cuenta solo q < UMBRAL_Q; `bajan` y `suben` separan los hallazgos
    por el signo del efecto (negativo = cuando sube lo primero, baja lo segundo).
    """
    return consultar(f"""
        SELECT eslabon,
               count(*) AS pruebas,
               count(*) FILTER (q_valor < {UMBRAL_Q}) AS hallazgos,
               count(*) FILTER (q_valor < {UMBRAL_Q} AND coeficiente < 0) AS bajan,
               count(*) FILTER (q_valor < {UMBRAL_Q} AND coeficiente > 0) AS suben,
               count(DISTINCT departamento) AS departamentos,
               count(DISTINCT departamento) FILTER (q_valor < {UMBRAL_Q}) AS departamentos_hallazgo,
               count(DISTINCT producto) AS productos
        FROM indicador_sensibilidad_clima
        GROUP BY eslabon
    """).set_index("eslabon")


@st.cache_data(ttl=TTL)
def sensibilidad_hallazgos() -> pd.DataFrame:
    """Solo las relaciones que se sostienen (q < UMBRAL_Q), de la mas segura a la menos."""
    return consultar(f"""
        SELECT eslabon, producto, departamento, rezago_meses, coeficiente, q_valor, n, metodo
        FROM indicador_sensibilidad_clima
        WHERE q_valor < {UMBRAL_Q}
        ORDER BY eslabon, q_valor
    """)


@st.cache_data(ttl=TTL)
def quiebres_resumen() -> pd.DataFrame:
    """Una fila por fecha probada: cuantos productos cambiaron su ritmo o su volatilidad.

    `ritmo` y `volatilidad` cuentan los quiebres que se sostienen (q < UMBRAL_Q).
    `ritmo_p` y `volatilidad_p` cuentan los que tienen p < 0,05 sin corregir: con
    33 productos, uno o dos salen asi por puro azar.
    """
    return consultar(f"""
        SELECT periodo_quiebre, any_value(fase_que_empieza) AS fase,
               count(DISTINCT producto) AS productos,
               count(DISTINCT producto) FILTER (q_valor < {UMBRAL_Q}) AS con_quiebre,
               count(*) FILTER (que_cambia = 'ritmo' AND q_valor < {UMBRAL_Q}) AS ritmo,
               count(*) FILTER (que_cambia = 'volatilidad' AND q_valor < {UMBRAL_Q}) AS volatilidad,
               count(*) FILTER (que_cambia = 'ritmo' AND p_valor < 0.05) AS ritmo_p,
               count(*) FILTER (que_cambia = 'volatilidad' AND p_valor < 0.05) AS volatilidad_p
        FROM indicador_quiebres
        GROUP BY periodo_quiebre
        ORDER BY periodo_quiebre
    """)


@st.cache_data(ttl=TTL)
def cadena(art_id: int, dpto_codigo: str, producto_diario: str | None = None) -> pd.DataFrame:
    """Lluvia, toneladas y precio del mismo articulo y departamento, mes por mes.

    Las tres series se unen por `periodo`, no por posicion de fila: cada una
    tiene su propia cobertura y sus propios huecos. Un mes sin dato queda nulo
    para que la grafica corte la linea en vez de inventar continuidad.

    Si llega `producto_diario` (ver `fuente_precio`), el precio sale del precio
    diario mensual de los mercados de ese departamento, desde 2020. Si no, del
    precio semanal (unos 13 meses).
    """
    mercados = mercados_diarios(dpto_codigo) if producto_diario else []
    if mercados:
        precio = f"""
            SELECT periodo, median(precio_cop_kg) AS precio, 'kg' AS unidad
            FROM fact_precio_mayorista
            WHERE producto = {_sql_texto(producto_diario)}
              AND mercado IN ({", ".join(_sql_texto(m) for m in mercados)})
            GROUP BY periodo"""
    else:
        precio = f"""
            SELECT periodo, median(precio) AS precio, any_value(unidad) AS unidad
            FROM fact_precio_semanal
            WHERE art_id = {int(art_id)} AND dpto_codigo = '{dpto_codigo}'
            GROUP BY periodo"""
    return consultar(f"""
        WITH lluvia AS (
            SELECT anio * 100 + mes AS periodo, sum(precipitacion_mm) AS lluvia_mm
            FROM (SELECT year(fecha) AS anio, month(fecha) AS mes, precipitacion_mm
                  FROM fact_clima_diario
                  WHERE dpto_codigo = '{dpto_codigo}' AND tipo = 'observado')
            GROUP BY anio, mes
        ), toneladas AS (
            SELECT periodo, sum(toneladas) AS toneladas
            FROM fact_abastecimiento
            WHERE art_id = {int(art_id)} AND dpto_codigo = '{dpto_codigo}'
            GROUP BY periodo
        ), precio AS ({precio}
        ), meses AS (
            SELECT periodo FROM lluvia
            UNION SELECT periodo FROM toneladas
            UNION SELECT periodo FROM precio
        )
        SELECT m.periodo, l.lluvia_mm, t.toneladas, p.precio, p.unidad
        FROM meses m
        LEFT JOIN lluvia l USING (periodo)
        LEFT JOIN toneladas t USING (periodo)
        LEFT JOIN precio p USING (periodo)
        ORDER BY m.periodo
    """)


# --- Clima de las zonas productoras -----------------------------------------


@st.cache_data(ttl=TTL)
def departamentos_clima() -> pd.DataFrame:
    """Zonas productoras con clima descargado."""
    return consultar("""
        SELECT DISTINCT departamento, dpto_codigo
        FROM fact_clima_diario ORDER BY departamento
    """)


@st.cache_data(ttl=TTL)
def clima_diario(dpto_codigo: str, dias: int = 60) -> pd.DataFrame:
    """Lluvia y temperatura por dia de un departamento: lo observado y el pronostico.

    `dias` acota solo lo observado; el pronostico (16 dias) entra completo.
    """
    return consultar(f"""
        SELECT fecha, precipitacion_mm, temp_max, temp_min, tipo
        FROM fact_clima_diario
        WHERE dpto_codigo = '{dpto_codigo}'
          AND (tipo = 'pronostico'
               OR fecha >= (SELECT max(fecha) FROM fact_clima_diario
                            WHERE tipo = 'observado') - INTERVAL '{int(dias)} days')
        ORDER BY fecha
    """)


@st.cache_data(ttl=TTL)
def pronostico_estacional(dpto_codigo: str) -> pd.DataFrame:
    """Lluvia esperada por mes (p10/p50/p90) y su diferencia con el promedio historico."""
    return consultar(f"""
        SELECT periodo, anio, mes, precip_p10, precip_p50, precip_p90, anomalia_p50
        FROM fact_pronostico_estacional
        WHERE dpto_codigo = '{dpto_codigo}'
        ORDER BY periodo
    """)


@st.cache_data(ttl=TTL)
def geojson_departamentos() -> dict:
    """Geometria de los 33 departamentos. La llave es `DPTO` (codigo DANE)."""
    import json

    ruta = CONFIG / "geo" / "colombia_departamentos.geojson"
    return json.loads(ruta.read_text(encoding="utf-8"))


@st.cache_data(ttl=TTL)
def mercados_geo() -> pd.DataFrame:
    """Coordenadas aproximadas (centro urbano) de cada mercado, para el mapa."""
    return pd.read_csv(CONFIG / "mercados.csv")


@st.cache_data(ttl=TTL)
def tabla_existe(nombre: str) -> bool:
    """True si la tabla esta en la base. Sirve para fuentes que aun no se cargaron."""
    return bool(consultar(
        f"SELECT count(*) AS n FROM duckdb_tables() WHERE table_name = '{nombre}'"
    )["n"][0])
