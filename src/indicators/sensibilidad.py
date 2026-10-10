"""Sensibilidad al clima: que tanto mueve el clima los precios, eslabon por eslabon.

La cadena que se mide:

    ONI (El Nino) -> lluvia en la zona -> toneladas que llegan -> precio

Cada eslabon responde una pregunta y usa el metodo que le corresponde:

| eslabon          | pregunta                                       | metodo                         |
|------------------|------------------------------------------------|--------------------------------|
| oni->lluvia      | El Nino cambia la lluvia de esta zona?         | correlacion de Pearson         |
| lluvia->oferta   | La lluvia cambia las toneladas que llegan?     | regresion + estacionalidad     |
| oferta->precio   | Menos toneladas = precio mas alto?             | panel con efectos fijos        |
| lluvia->precio   | Efecto total de la lluvia sobre el precio      | regresion + estacionalidad     |

Por que el panel solo en oferta->precio: Malau et al. (2021) usan un panel de
provincias porque cada provincia tiene SU lluvia. Aca la lluvia que importa es la
de la zona productora, la misma para los 20 mercados: un panel por mercado
contaria 20 veces el mismo dato de lluvia e inflaria la significancia. Las
toneladas, en cambio, si son distintas en cada departamento.

Reglas que se cuidan:
- Cambios solo entre meses seguidos (el hueco de 2021 de SIPSA no se cruza).
- Rezagos en meses de calendario, nunca corriendo filas.
- "Estacionalidad" = un efecto propio para cada mes del ano. Sin el, la lluvia y
  los precios se moverian juntos solo porque los dos cambian con las temporadas.
- Con muchas pruebas a la vez algo sale "significativo" por suerte: por eso cada
  resultado trae su q-valor (Benjamini-Hochberg). Lo que se debe mirar es q < 0,1.
- Correlacion no es causalidad: esto senala pistas, no demuestra causas.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.indicators.vigilancia import rezagar, retornos_nacionales
from src.indicators.volatilidad import _distancia_en_meses

REZAGOS_ONI = range(0, 7)      # el efecto de El Nino tarda varios meses en llegar
REZAGOS_LLUVIA = range(0, 4)
MINIMO_MESES = 24              # menos que esto no alcanza para una conclusion


# --- Herramientas -----------------------------------------------------------------

def ols(y: pd.Series, x: pd.DataFrame, efectos: dict[str, pd.Series] | None = None) -> dict:
    """Minimos cuadrados. Devuelve el coeficiente de la PRIMERA columna de `x`.

    `efectos` son variables de grupo (mes del ano, departamento): cada grupo
    recibe su propio nivel, asi el coeficiente mide solo lo que cambia DENTRO
    de cada grupo. Eso es un "efecto fijo".

    El p-valor usa la aproximacion normal (sin scipy); con 40 o mas datos la
    diferencia con la t de Student es minima.
    """
    datos = pd.concat([y.rename("_y"), x], axis=1)
    for nombre, grupo in (efectos or {}).items():
        datos = datos.join(pd.get_dummies(grupo, prefix=nombre, drop_first=True, dtype=float))
    datos = datos.dropna()
    n = len(datos)
    matriz = np.column_stack([np.ones(n), datos.drop(columns="_y").to_numpy(dtype=float)])
    objetivo = datos["_y"].to_numpy(dtype=float)
    libres = n - matriz.shape[1]
    if libres < 2:
        return {"coeficiente": np.nan, "p_valor": np.nan, "n": n}

    beta, *_ = np.linalg.lstsq(matriz, objetivo, rcond=None)
    residuos = objetivo - matriz @ beta
    varianza = residuos @ residuos / libres
    error = math.sqrt(varianza * np.linalg.pinv(matriz.T @ matriz)[1, 1])
    t = beta[1] / error if error > 0 else np.inf
    return {"coeficiente": float(beta[1]), "p_valor": math.erfc(abs(t) / math.sqrt(2)), "n": n}


def q_valores(p: pd.Series) -> pd.Series:
    """Benjamini-Hochberg: corrige los p-valores por haber hecho muchas pruebas."""
    orden = p.sort_values()
    m = len(orden)
    q = orden * m / np.arange(1, m + 1)
    q = q[::-1].cummin()[::-1].clip(upper=1)   # nunca puede bajar al subir en el orden
    return q.reindex(p.index)


def cambio_log(df: pd.DataFrame, llaves: list[str], columna: str) -> pd.DataFrame:
    """Cambio logaritmico mes a mes de cada serie, solo entre meses seguidos."""
    df = df.sort_values(llaves + ["periodo"]).copy()
    previo = df.groupby(llaves)[columna].shift(1)
    salto = _distancia_en_meses(df.groupby(llaves)["periodo"].shift(1), df["periodo"])
    valido = (df[columna] > 0) & (previo > 0) & (salto == 1)
    # Se anula ANTES del logaritmo: asi nunca se calcula log(0) ni log de un negativo
    df["cambio"] = np.log((df[columna] / previo).where(valido))
    return df


def mapa_articulos(productos: pd.Series, articulos: pd.DataFrame) -> pd.DataFrame:
    """Producto del precio diario -> articulo del abastecimiento, SOLO si el nombre
    es identico (sin el asterisco y sin importar mayusculas).

    Asi quedan fuera los que mezclarian variedades: "Papa negra*" agrupa varias
    papas que el abastecimiento separa, y "Tomate*" no es "Tomate de arbol".
    """
    base = productos.drop_duplicates().to_frame("producto")
    base["llave"] = base["producto"].str.replace("*", "", regex=False).str.strip().str.lower()
    arts = articulos.drop_duplicates("art_id").assign(llave=lambda d: d["articulo"].str.strip().str.lower())
    return base.merge(arts[["llave", "art_id", "articulo"]], on="llave").drop(columns="llave")


def _mes(df: pd.DataFrame) -> pd.Series:
    return df["periodo"] % 100


def _fila(eslabon, producto, art_id, departamento, variable, rezago, resultado, metodo) -> dict:
    return {"eslabon": eslabon, "producto": producto, "art_id": art_id, "departamento": departamento,
            "variable": variable, "rezago_meses": rezago, **resultado, "metodo": metodo}


# --- Eslabones ----------------------------------------------------------------------

def lluvia_por_zona(clima: pd.DataFrame) -> pd.DataFrame:
    """Anomalia de lluvia por departamento y mes (la misma para todos sus productos)."""
    return (clima.groupby(["departamento", "periodo"], as_index=False)["precipitacion_anomalia"]
            .mean().rename(columns={"precipitacion_anomalia": "lluvia"}))


def oni_lluvia(enso: pd.DataFrame, clima: pd.DataFrame) -> list[dict]:
    """Paso 1 de Malau: en que departamentos El Nino cambia la lluvia, y con cuanto rezago."""
    oni = enso.assign(periodo=enso["anio"] * 100 + enso["mes"])[["periodo", "anomalia"]]
    filas = []
    for depto, lluvia in lluvia_por_zona(clima).groupby("departamento"):
        for k in REZAGOS_ONI:
            cruce = lluvia.merge(rezagar(oni, k), on="periodo").dropna()
            n = len(cruce)
            if n < MINIMO_MESES:
                continue
            r = cruce["lluvia"].corr(cruce["anomalia"])
            t = r * math.sqrt((n - 2) / max(1 - r * r, 1e-12))
            filas.append(_fila("oni->lluvia", None, None, depto, "oni", k,
                               {"coeficiente": r, "p_valor": math.erfc(abs(t) / math.sqrt(2)), "n": n},
                               "correlacion_pearson"))
    return filas


def lluvia_oferta(abas: pd.DataFrame, clima: pd.DataFrame, puente: pd.DataFrame, mapa: pd.DataFrame) -> list[dict]:
    """Cambio de las toneladas que llegan al pais vs. la lluvia de la zona de hace k meses."""
    lluvia = lluvia_por_zona(clima)
    filas = []
    for _, z in puente.merge(mapa, left_on="producto_sipsa", right_on="producto").iterrows():
        toneladas = (abas[abas["art_id"] == z["art_id"]].groupby("periodo", as_index=False)["toneladas"].sum()
                     .assign(serie=1))
        cambio = cambio_log(toneladas, ["serie"], "toneladas")[["periodo", "cambio"]]
        zona = lluvia[lluvia["departamento"] == z["departamento"]][["periodo", "lluvia"]]
        for k in REZAGOS_LLUVIA:
            cruce = cambio.merge(rezagar(zona, k), on="periodo")
            r = ols(cruce["cambio"], cruce[["lluvia"]], efectos={"mes": _mes(cruce)})
            if r["n"] >= MINIMO_MESES:
                filas.append(_fila("lluvia->oferta", z["producto_sipsa"], z["art_id"], z["departamento"],
                                   "lluvia", k, r, "regresion_estacional"))
    return filas


def oferta_precio_panel(df: pd.DataFrame) -> dict:
    """Panel departamento x mes: cambio del precio vs. cambio de las toneladas.

    Efectos fijos de departamento (cada uno con su propia tendencia de base) y de
    mes del ano (temporadas). El coeficiente se lee como elasticidad: -0,5 es
    "1 % mas de toneladas, 0,5 % menos de precio".
    """
    precio = cambio_log(df, ["dpto_codigo"], "precio").rename(columns={"cambio": "cambio_precio"})
    toneladas = cambio_log(df, ["dpto_codigo"], "toneladas")[["dpto_codigo", "periodo", "cambio"]]
    cruce = precio.merge(toneladas, on=["dpto_codigo", "periodo"])
    return ols(cruce["cambio_precio"], cruce[["cambio"]],
               efectos={"dpto": cruce["dpto_codigo"], "mes": _mes(cruce)})


def oferta_precio(precios: pd.DataFrame, abas: pd.DataFrame, mercados: pd.DataFrame, mapa: pd.DataFrame) -> list[dict]:
    """Paso 2 de Malau, con la oferta en el medio: un panel por producto."""
    precios = precios.merge(mercados[["mercado", "dpto_codigo"]], on="mercado")
    filas = []
    for _, m in mapa.iterrows():
        p = precios[precios["producto"] == m["producto"]][["dpto_codigo", "periodo", "precio_cop_kg"]]
        t = (abas[abas["art_id"] == m["art_id"]].groupby(["dpto_codigo", "periodo"], as_index=False)["toneladas"].sum())
        df = p.rename(columns={"precio_cop_kg": "precio"}).merge(t, on=["dpto_codigo", "periodo"])
        r = oferta_precio_panel(df)
        if r["n"] >= MINIMO_MESES:
            filas.append(_fila("oferta->precio", m["producto"], m["art_id"], None, "abastecimiento", 0, r,
                               "panel_efectos_fijos"))
    return filas


def lluvia_precio(precios: pd.DataFrame, clima: pd.DataFrame, puente: pd.DataFrame) -> list[dict]:
    """Efecto total: cambio del precio nacional vs. la lluvia de la zona de hace k meses."""
    ret = retornos_nacionales(precios)[["producto", "periodo", "retorno"]]
    lluvia = lluvia_por_zona(clima)
    filas = []
    for _, z in puente.iterrows():
        serie = ret[ret["producto"] == z["producto_sipsa"]]
        zona = lluvia[lluvia["departamento"] == z["departamento"]][["periodo", "lluvia"]]
        for k in REZAGOS_LLUVIA:
            cruce = serie.merge(rezagar(zona, k), on="periodo")
            r = ols(cruce["retorno"], cruce[["lluvia"]], efectos={"mes": _mes(cruce)})
            if r["n"] >= MINIMO_MESES:
                filas.append(_fila("lluvia->precio", z["producto_sipsa"], None, z["departamento"],
                                   "lluvia", k, r, "regresion_estacional"))
    return filas


# --- Tabla final ----------------------------------------------------------------------

def construir(con) -> pd.DataFrame:
    """Lee el modelo, calcula los cuatro eslabones y agrega el q-valor por eslabon."""
    leer = lambda sql: con.execute(sql).df()
    precios = leer("SELECT mercado, producto, anio, mes, periodo, precio_cop_kg, mes_cerrado "
                   "FROM fact_precio_mayorista")
    precios = precios[precios["mes_cerrado"]]          # el mes en curso todavia no es definitivo
    clima = leer("SELECT departamento, periodo, precipitacion_anomalia FROM fact_clima")
    enso = leer("SELECT anio, mes, anomalia FROM fact_enso")
    puente = leer("SELECT producto_sipsa, departamento FROM puente_zona_sipsa")
    mercados = leer("SELECT mercado, dpto_codigo FROM dim_mercado")
    abas = leer("SELECT art_id, articulo, dpto_codigo, periodo, toneladas FROM fact_abastecimiento")
    mapa = mapa_articulos(precios["producto"], abas[["art_id", "articulo"]])

    filas = (oni_lluvia(enso, clima) + lluvia_oferta(abas, clima, puente, mapa)
             + oferta_precio(precios, abas, mercados, mapa) + lluvia_precio(precios, clima, puente))
    tabla = pd.DataFrame(filas)
    tabla["q_valor"] = tabla.groupby("eslabon")["p_valor"].transform(q_valores)
    return tabla
