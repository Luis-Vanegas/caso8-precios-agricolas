"""Indicadores de volatilidad y alerta temprana sobre precios mayoristas.

Los umbrales son configurables y NO son estandares oficiales: son convenciones
de este trabajo y asi hay que presentarlos.

Por que sobre SIPSA y no sobre FAOSTAT: la deteccion temprana necesita
frecuencia. SIPSA publica a diario y agregamos a mensual; FAOSTAT publica una
vez al ano con un ano de rezago, con lo cual no puede detectar nada temprano.
FAOSTAT aporta el contexto estructural, no la alerta.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# Ventana de la volatilidad movil, en meses. Doce captura el ciclo estacional
# completo, que en agricultura es lo que importa.
VENTANA = 12

# Minimo de observaciones para que una volatilidad sea creible. Con menos, la
# desviacion estandar es ruido con aspecto de indicador.
MINIMO_OBSERVACIONES = 6

# Umbrales del semaforo, en desviaciones estandar del retorno del mes frente a
# la historia de esa misma serie.
UMBRAL_AMARILLA = 2.0
UMBRAL_ROJA = 3.0

CLAVES_SERIE = ["mercado", "producto"]


def retornos(df: pd.DataFrame, columna: str = "precio_cop_kg") -> pd.DataFrame:
    """Agrega el retorno logaritmico mes a mes de cada serie.

    Se usa logaritmo y no variacion porcentual porque el logaritmo es simetrico:
    subir 50% y bajar 33% se compensan exactamente, mientras que en porcentaje
    no, y eso sesga cualquier promedio o desviacion que se calcule despues.
    """
    df = df.sort_values(CLAVES_SERIE + ["periodo"]).copy()
    previo = df.groupby(CLAVES_SERIE, dropna=False)[columna].shift(1)
    # Solo tiene sentido con precios positivos; un cero o un nulo daria -inf.
    valido = (df[columna] > 0) & (previo > 0)
    df["retorno_log"] = np.where(valido, np.log(df[columna] / previo), np.nan)

    # Un salto de periodo rompe la continuidad: el retorno entre enero y junio
    # no es comparable con uno mes a mes.
    periodo_previo = df.groupby(CLAVES_SERIE, dropna=False)["periodo"].shift(1)
    df["meses_desde_anterior"] = _distancia_en_meses(periodo_previo, df["periodo"])
    df.loc[df["meses_desde_anterior"] != 1, "retorno_log"] = np.nan
    return df


def _distancia_en_meses(desde: pd.Series, hasta: pd.Series) -> pd.Series:
    """Meses entre dos periodos con formato AAAAMM."""
    a_anio, a_mes = desde // 100, desde % 100
    b_anio, b_mes = hasta // 100, hasta % 100
    return (b_anio - a_anio) * 12 + (b_mes - a_mes)


def volatilidad(df: pd.DataFrame, ventana: int = VENTANA) -> pd.DataFrame:
    """Agrega la desviacion estandar movil del retorno logaritmico."""
    df = retornos(df) if "retorno_log" not in df.columns else df.copy()
    agrupado = df.groupby(CLAVES_SERIE, dropna=False)["retorno_log"]
    df["volatilidad"] = agrupado.transform(
        lambda s: s.rolling(ventana, min_periods=MINIMO_OBSERVACIONES).std()
    )
    # Anualizar permite comparar contra volatilidades de otros activos, que se
    # publican siempre en base anual.
    df["volatilidad_anualizada"] = df["volatilidad"] * np.sqrt(12)
    return df


def alertas(df: pd.DataFrame) -> pd.DataFrame:
    """Clasifica cada mes en verde, amarilla o roja segun el z-score del retorno.

    El z-score se calcula con la media y desviacion de TODA la historia previa
    de la serie, no de la ventana movil: la pregunta es si este mes es raro
    para este producto en este mercado, no si es raro comparado con el ultimo ano.
    """
    df = volatilidad(df) if "volatilidad" not in df.columns else df.copy()
    agrupado = df.groupby(CLAVES_SERIE, dropna=False)["retorno_log"]

    # expanding() usa solo el pasado y el presente, nunca el futuro. Usar la
    # media de toda la serie filtraria informacion que en su momento no existia.
    media = agrupado.transform(lambda s: s.expanding(MINIMO_OBSERVACIONES).mean())
    desviacion = agrupado.transform(lambda s: s.expanding(MINIMO_OBSERVACIONES).std())

    df["z_score"] = (df["retorno_log"] - media) / desviacion.replace(0, np.nan)
    df["alerta"] = pd.cut(
        df["z_score"].abs(),
        bins=[-np.inf, UMBRAL_AMARILLA, UMBRAL_ROJA, np.inf],
        labels=["verde", "amarilla", "roja"],
    )
    # Sin z-score no hay alerta; dejarlo en "verde" seria afirmar que esta bien
    # cuando en realidad no se sabe.
    df.loc[df["z_score"].isna(), "alerta"] = None
    df["direccion"] = np.where(df["retorno_log"] > 0, "alza", "baja")
    return df


def resumen_por_producto(df: pd.DataFrame) -> pd.DataFrame:
    """Una fila por producto con su volatilidad tipica y sus alertas historicas."""
    if "alerta" not in df.columns:
        df = alertas(df)
    return (
        df.groupby("producto", dropna=False)
        .agg(
            mercados=("mercado", "nunique"),
            meses=("periodo", "nunique"),
            volatilidad_mediana=("volatilidad_anualizada", "median"),
            alertas_rojas=("alerta", lambda s: int((s == "roja").sum())),
            alertas_amarillas=("alerta", lambda s: int((s == "amarilla").sum())),
            precio_ultimo=("precio_cop_kg", "last"),
        )
        .reset_index()
        .sort_values("volatilidad_mediana", ascending=False)
    )


def dependencia_importaciones(comercio: pd.DataFrame, produccion: pd.DataFrame) -> pd.DataFrame:
    """imp / (prod + imp - exp) * 100, por item y anio, solo en toneladas.

    Mide que porcion del consumo aparente viene de afuera. Un valor alto expone
    el precio interno a la tasa de cambio y al precio internacional.
    """
    def _sumar(df, elemento, nombre):
        sub = df[(df["elemento"] == elemento) & (df["unidad"] == "t")]
        return (
            sub.groupby(["item_codigo", "anio"], dropna=False)["valor"]
            .sum()
            .reset_index()
            .rename(columns={"valor": nombre})
        )

    cruce = (
        _sumar(produccion, "Production", "produccion")
        .merge(_sumar(comercio, "Import quantity", "importacion"), on=["item_codigo", "anio"], how="outer")
        .merge(_sumar(comercio, "Export quantity", "exportacion"), on=["item_codigo", "anio"], how="outer")
        .fillna({"produccion": 0, "importacion": 0, "exportacion": 0})
    )
    cruce["consumo_aparente"] = cruce["produccion"] + cruce["importacion"] - cruce["exportacion"]
    # Un consumo aparente nulo o negativo no admite porcentaje: se deja vacio en
    # vez de producir un numero que parezca valido.
    cruce["dependencia_pct"] = np.where(
        cruce["consumo_aparente"] > 0,
        100 * cruce["importacion"] / cruce["consumo_aparente"],
        np.nan,
    ).round(2)
    return cruce
