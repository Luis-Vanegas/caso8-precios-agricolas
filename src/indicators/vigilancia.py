"""Lista de vigilancia: pistas de lo que puede pasar el proximo mes.

Esto NO es un modelo de prediccion. Es una regla simple y explicable:

  1. Para cada producto y su zona productora, se mide si la lluvia de hace
     k meses (k = 1, 2 o 3) se ha movido historicamente junto con el cambio de
     precio (correlacion de Spearman).
  2. Solo se usan las parejas con una relacion de al menos |rho| >= 0,3 y con
     24 meses o mas de historia.
  3. Para el proximo mes se mira la lluvia de hace k meses (que ya se conoce)
     y se multiplica su signo por el de rho: si da positivo, hay presion al
     alza del precio; si da negativo, a la baja.

Limites que hay que decir en voz alta: son pocas parejas (con datos a sept.
2026, 2 de 36 con rezago de 1 a 3 meses), la correlacion no es causalidad y
cada pareja tiene unos 65 meses. Ver `acierto_historico`.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from src.indicators.volatilidad import retornos

REZAGOS = (0, 1, 2, 3)
MINIMO_MESES = 24
UMBRAL_RHO = 0.3


def retornos_nacionales(precios: pd.DataFrame) -> pd.DataFrame:
    """Mediana nacional del precio por producto y mes, y su retorno logaritmico.

    Reusa `retornos`, que anula el cambio cuando hay un salto de meses
    (el hueco de 2021 de SIPSA). Solo usa meses cerrados.
    """
    # El mes en curso tiene pocos dias: su cambio todavia no es definitivo.
    if "mes_cerrado" in precios.columns:
        precios = precios[precios["mes_cerrado"]]
    nacional = (
        precios.groupby(["producto", "anio", "mes", "periodo"], as_index=False)["precio_cop_kg"]
        .median()
        .assign(mercado="nacional")
    )
    return retornos(nacional).rename(columns={"retorno_log": "retorno"})


def _spearman(a: pd.Series, b: pd.Series) -> float:
    """Spearman = Pearson sobre los rangos. Asi no se depende de scipy."""
    return float(a.rank().corr(b.rank()))


def rezagar(serie: pd.DataFrame, k: int) -> pd.DataFrame:
    """Corre `periodo` k meses hacia adelante: el dato de t-k queda etiquetado en t.

    Se hace sobre la serie de clima COMPLETA y luego se une por mes. Asi "hace k
    meses" es siempre calendario real, incluso cuando SIPSA no tiene precios
    (el hueco de 2021). Correr filas con shift() daria meses equivocados.
    """
    periodos = pd.PeriodIndex(serie["periodo"].astype(str), freq="M") + k
    return serie.assign(periodo=periodos.strftime("%Y%m").astype(int))


def correlacion_rezagada(ret: pd.DataFrame, variable: pd.DataFrame, llaves: list[str],
                         columna: str, rezagos=REZAGOS, minimo: int = MINIMO_MESES) -> pd.DataFrame:
    """Spearman entre el retorno del mes t y `columna` del mes t-k.

    ret:      producto, periodo, retorno (+ las `llaves` si la variable es por zona)
    variable: periodo, `columna` y las `llaves` (por ejemplo departamento y producto_zona)
    """
    filas = []
    grupos = ["producto"] + [l for l in llaves if l in ret.columns and l != "producto"]
    for k in rezagos:
        cruce = ret.merge(rezagar(variable[llaves + ["periodo", columna]], k),
                          on=llaves + ["periodo"], how="inner").dropna(subset=["retorno", columna])
        for claves, g in cruce.groupby(grupos):
            if len(g) >= minimo:
                fila = dict(zip(grupos, claves if isinstance(claves, tuple) else (claves,)))
                filas.append({**fila, "variable": columna, "rezago": k, "n": len(g),
                              "spearman": round(_spearman(g["retorno"], g[columna]), 3)})
    return pd.DataFrame(filas)


def correlacion_lluvia(ret: pd.DataFrame, clima: pd.DataFrame, puente: pd.DataFrame,
                       rezagos=REZAGOS) -> pd.DataFrame:
    """Atajo: retorno de cada producto contra la lluvia de SU zona productora."""
    con_zona = ret.merge(puente, left_on="producto", right_on="producto_sipsa")
    lluvia = clima.rename(columns={"producto": "producto_zona"})
    lluvia = lluvia.assign(periodo=lluvia["anio"] * 100 + lluvia["mes"])
    return correlacion_rezagada(con_zona, lluvia, ["producto_zona", "departamento"],
                                "precipitacion_anomalia", rezagos)


def senales(correlaciones: pd.DataFrame, clima: pd.DataFrame, puente: pd.DataFrame,
            proximo_periodo: int, umbral: float = UMBRAL_RHO) -> pd.DataFrame:
    """Pistas para `proximo_periodo` (AAAAMM) con las parejas de relacion fuerte.

    El rezago 0 no sirve para anticipar (seria la lluvia del mismo mes que
    todavia no ha pasado), asi que solo entran k >= 1.
    """
    fuertes = correlaciones[(correlaciones["variable"] == "precipitacion_anomalia")
                            & (correlaciones["rezago"] >= 1)
                            & (correlaciones["spearman"].abs() >= umbral)].copy()
    if fuertes.empty:
        return fuertes.assign(periodo_lluvia=[], anomalia=[], senal=[])

    proximo = pd.Period(str(proximo_periodo), freq="M")
    fuertes["periodo_lluvia"] = [int((proximo - k).strftime("%Y%m")) for k in fuertes["rezago"]]

    zona = puente[["producto_sipsa", "producto_zona", "departamento"]].rename(
        columns={"producto_sipsa": "producto"})
    lluvia = clima.assign(periodo_lluvia=clima["anio"] * 100 + clima["mes"]).rename(
        columns={"producto": "producto_zona"})[
        ["producto_zona", "departamento", "periodo_lluvia", "precipitacion_anomalia"]]
    # Tipos fijos: con una tabla de clima vacia, pandas los deja como texto y la union falla.
    lluvia = lluvia.astype({"periodo_lluvia": "int64", "precipitacion_anomalia": "float64"})
    fuertes = (fuertes.drop(columns=["producto_zona"], errors="ignore")
               .merge(zona, on=["producto", "departamento"])
               .merge(lluvia, on=["producto_zona", "departamento", "periodo_lluvia"], how="left")
               .rename(columns={"precipitacion_anomalia": "anomalia"}))

    direccion = np.sign(fuertes["spearman"]) * np.sign(fuertes["anomalia"])
    fuertes["senal"] = np.select([direccion > 0, direccion < 0], ["al alza", "a la baja"], "sin dato")
    fuertes.loc[fuertes["anomalia"].isna(), "senal"] = "sin dato"
    return fuertes.drop(columns="producto_zona").sort_values("spearman", key=abs, ascending=False)


def acierto_historico(ret: pd.DataFrame, clima: pd.DataFrame, puente: pd.DataFrame,
                      correlaciones: pd.DataFrame, umbral: float = UMBRAL_RHO) -> pd.DataFrame:
    """Que tan seguido la senal habria acertado la direccion del precio en el pasado.

    Para cada pareja fuerte (k >= 1) y cada mes con dato: acierto si el signo de
    rho x anomalia(t-k) coincide con el signo del retorno de t. Tirar una moneda
    acierta el 50 %.

    Ojo: rho se calculo con estos mismos meses, asi que la cifra es optimista
    (evaluacion "dentro de muestra"). Sirve para descartar pistas malas, no para
    prometer que las buenas van a funcionar.
    """
    fuertes = correlaciones[(correlaciones["variable"] == "precipitacion_anomalia")
                            & (correlaciones["rezago"] >= 1)
                            & (correlaciones["spearman"].abs() >= umbral)]
    con_zona = ret.merge(puente, left_on="producto", right_on="producto_sipsa")
    lluvia = clima.rename(columns={"producto": "producto_zona"})
    lluvia = lluvia.assign(periodo=lluvia["anio"] * 100 + lluvia["mes"])[
        ["producto_zona", "departamento", "periodo", "precipitacion_anomalia"]]

    filas = []
    for f in fuertes.itertuples():
        serie = con_zona[(con_zona["producto"] == f.producto) & (con_zona["departamento"] == f.departamento)]
        cruce = serie.merge(rezagar(lluvia, f.rezago), on=["producto_zona", "departamento", "periodo"])
        cruce = cruce.dropna(subset=["retorno", "precipitacion_anomalia"])
        cruce = cruce[(cruce["retorno"] != 0) & (cruce["precipitacion_anomalia"] != 0)]
        senal = np.sign(f.spearman) * np.sign(cruce["precipitacion_anomalia"])
        aciertos = int((senal == np.sign(cruce["retorno"])).sum())
        filas.append({"producto": f.producto, "departamento": f.departamento, "rezago": f.rezago,
                      "meses": len(cruce), "aciertos": aciertos,
                      "tasa_acierto": round(aciertos / len(cruce), 3) if len(cruce) else np.nan})
    return pd.DataFrame(filas)
