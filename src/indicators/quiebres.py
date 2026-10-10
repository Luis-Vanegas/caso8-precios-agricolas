"""Quiebres estructurales: el precio cambio de comportamiento cuando empezo El Nino?

Dos preguntas, dos pruebas, en cada fecha candidata:
- ritmo:       el cambio mensual promedio es distinto antes y despues? (Chow)
- volatilidad: los precios se mueven mas (o menos) despues?   (Brown-Forsythe)

Es la prueba del enlace que encontro el equipo (statisticshowto.com/chow-test).
OJO: en Malau et al. (2021) el "Chow test" es otra cosa (elegir entre un panel
con o sin efectos fijos). Aca se usa en su sentido clasico: quiebre estructural.

La formula de Chow, con k parametros por tramo (aca k = 1, el promedio):

    F = ((SCR_todo - (SCR_antes + SCR_despues)) / k) / ((SCR_antes + SCR_despues) / (n - 2k))

SCR = suma de residuos al cuadrado. Si dos tramos separados ajustan MUCHO mejor
que uno solo, F es grande y hay quiebre. Brown-Forsythe es el mismo calculo pero
sobre la distancia de cada dato a la mediana de su tramo: compara la dispersion.

Tres trampas que se evitan (medidas con los datos reales el 2026-10-09):
1. Inflacion comun: en 2022-2023 TODOS los alimentos subieron y luego frenaron.
   Sin descontarla, casi cualquier fecha "rompe" (81 de 99 pruebas). Se usa el
   precio RELATIVO: el del producto frente a la mediana de la canasta ese mes.
2. Autocorrelacion: Chow supone que el error de un mes no depende del anterior.
   En NIVELES de precio esa dependencia es 0,67 (un precio alto sigue alto) y la
   prueba ve quiebres falsos (50 de 99 aun con precio relativo). En CAMBIOS
   mensuales baja a 0,11, y ahi la prueba es valida. Por eso se prueba sobre cambios.
3. Fechas al azar: probar todas las fechas encuentra un quiebre siempre. Solo se
   prueban inicios de fase ENSO (razon fisica previa) con meses suficientes a
   cada lado, y se corrige con el q-valor.

Con k = 1, F se lee como un z al cuadrado y el p-valor sale de la normal.
Con ~30 meses por tramo la prueba solo ve cambios grandes: "no hay evidencia de
quiebre" no es lo mismo que "no hubo ningun efecto".
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from src.indicators.sensibilidad import cambio_log, q_valores

MINIMO_MESES = 18      # meses con precio a cada lado de la fecha


def _f_a_p(f: float) -> float:
    """p-valor de un F con 1 grado de libertad en el numerador (F = z^2)."""
    return math.erfc(math.sqrt(max(f, 0) / 2))


def chow_media(antes: pd.Series, despues: pd.Series) -> dict:
    """Chow con k = 1: el promedio de antes es distinto del de despues?"""
    todo = pd.concat([antes, despues])
    scr_todo = ((todo - todo.mean()) ** 2).sum()
    separadas = ((antes - antes.mean()) ** 2).sum() + ((despues - despues.mean()) ** 2).sum()
    f = (scr_todo - separadas) / (separadas / (len(todo) - 2))
    return {"f": f, "p_valor": _f_a_p(f), "valor_antes": antes.mean(), "valor_despues": despues.mean()}


def brown_forsythe(antes: pd.Series, despues: pd.Series) -> dict:
    """Chow sobre la distancia a la mediana de cada tramo: cambio la dispersion?

    Se reportan las desviaciones estandar de cada tramo (la volatilidad)."""
    r = chow_media((antes - antes.median()).abs(), (despues - despues.median()).abs())
    return {**r, "valor_antes": antes.std(), "valor_despues": despues.std()}


def precio_relativo(df: pd.DataFrame) -> pd.DataFrame:
    """Precio de cada producto dividido por la mediana de la canasta del mismo mes.

    Si todo sube 10 %, el relativo no cambia: asi se descuenta la inflacion comun."""
    log = np.log(df["precio"])
    canasta = log.groupby(df["periodo"]).transform("median")
    return df.assign(relativo=np.exp(log - canasta))


def cambios_sin_temporada(df: pd.DataFrame) -> pd.DataFrame:
    """Cambio log mensual del precio relativo (solo meses seguidos), menos el cambio
    promedio de ese mes del ano para ese producto (asi se quita la temporada)."""
    c = cambio_log(precio_relativo(df), ["producto"], "relativo").dropna(subset=["cambio"])
    mes = c["periodo"] % 100
    return c.assign(cambio=c["cambio"] - c.groupby(["producto", mes])["cambio"].transform("mean"))


def candidatos(enso: pd.DataFrame, periodos_precio: pd.Series, minimo: int = MINIMO_MESES) -> pd.DataFrame:
    """Inicios de fase ENSO con al menos `minimo` meses de precio antes y despues."""
    p = periodos_precio.drop_duplicates()
    ok = [(p < c).sum() >= minimo and (p >= c).sum() >= minimo for c in enso["periodo"]]
    return enso[ok].reset_index(drop=True)


def inicios_de_fase(enso: pd.DataFrame, desde: int) -> pd.DataFrame:
    """Meses en que la fase ENSO cambia respecto al mes anterior."""
    e = enso.assign(periodo=enso["anio"] * 100 + enso["mes"]).sort_values("periodo")
    cambia = e["fase"] != e["fase"].shift(1)
    return e[cambia & (e["periodo"] >= desde)][["periodo", "fase"]].reset_index(drop=True)


def construir(con) -> pd.DataFrame:
    """Ritmo y volatilidad de cada producto (mediana nacional) en cada fecha candidata."""
    precios = con.execute(
        "SELECT producto, periodo, median(precio_cop_kg) AS precio FROM fact_precio_mayorista "
        "WHERE mes_cerrado GROUP BY producto, periodo").df()
    enso = con.execute("SELECT anio, mes, fase FROM fact_enso").df()
    fechas = candidatos(inicios_de_fase(enso, int(precios["periodo"].min())), precios["periodo"])
    cambios = cambios_sin_temporada(precios)

    filas = []
    for producto, serie in cambios.groupby("producto"):
        for _, c in fechas.iterrows():
            antes = serie.loc[serie["periodo"] < c["periodo"], "cambio"]
            despues = serie.loc[serie["periodo"] >= c["periodo"], "cambio"]
            if min(len(antes), len(despues)) < MINIMO_MESES:
                continue
            for que, prueba in (("ritmo", chow_media), ("volatilidad", brown_forsythe)):
                r = prueba(antes, despues)
                filas.append({"producto": producto, "mercado": "nacional",
                              "periodo_quiebre": int(c["periodo"]), "fase_que_empieza": c["fase"],
                              "que_cambia": que, "f_chow": r["f"], "p_valor": r["p_valor"],
                              # en % por mes: promedio (ritmo) o desviacion estandar (volatilidad)
                              "valor_antes_pct": r["valor_antes"] * 100,
                              "valor_despues_pct": r["valor_despues"] * 100,
                              "n_antes": len(antes), "n_despues": len(despues)})
    tabla = pd.DataFrame(filas)
    tabla["q_valor"] = tabla.groupby("que_cambia")["p_valor"].transform(q_valores)
    tabla["hay_quiebre"] = tabla["q_valor"] < 0.1
    return tabla
