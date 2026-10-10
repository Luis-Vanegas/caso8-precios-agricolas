"""Pronostico del precio a 1, 2 y 3 meses, validado contra el pasado.

El modelo (una regresion, sin librerias extra) pronostica el CAMBIO del precio
desde hoy hasta dentro de h meses con lo que ya se sabe hoy:
  - la temporada del mes de destino (cada mes del ano tiene su cambio tipico),
  - la inercia: cuanto cambio el ultimo mes,
  - El Nino (ONI de hoy) y la anomalia de lluvia de hoy en la zona productora.

Se compara contra dos rivales ingenuos:
  - "sin cambio":  el precio se queda como esta hoy,
  - "estacional":  cambia como cambio el ano pasado entre esos mismos meses.

Reglas de honestidad:
1. Validacion sin trampa: para cada uno de los ultimos 24 meses se entrena SOLO
   con lo que se sabia ese mes y se pronostica el siguiente (backtest). Cambiar
   el futuro no cambia ningun pronostico del pasado (hay una prueba de eso).
2. Si el modelo no le gana al mejor ingenuo (por al menos 5 %), se presenta el
   ingenuo y se dice.
3. La banda del 80 % sale de los errores REALES del backtest (percentiles 10 y
   90), no de una formula teorica.
4. Horizontes en meses de calendario: no se cruza el hueco de 2021.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

ORIGENES_BACKTEST = 24     # ultimos meses en que se simula "pronosticar en vivo"
MINIMO_ENTRENAMIENTO = 24  # filas minimas para ajustar la regresion
MESES = range(1, 13)
# Para declararse ganador el modelo debe errar al menos 5 % menos que el ingenuo:
# con 24 meses de prueba, una diferencia menor es ruido (un empate no es victoria).
MARGEN_PARA_GANAR = 0.95


def _n(periodo):
    """Periodo AAAAMM -> numero de mes corrido (para sumar y restar meses)."""
    return periodo // 100 * 12 + periodo % 100


def _periodo(n):
    return (n - 1) // 12 * 100 + (n - 1) % 12 + 1


def armar_filas(serie: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Una fila por mes de origen con su destino a `horizonte` meses de calendario."""
    s = serie.set_index(_n(serie["periodo"]))
    lp = s["log_precio"]
    filas = []
    for n_origen, fila in s.iterrows():
        n_destino = n_origen + horizonte
        if n_destino not in lp.index:            # destino inexistente o al otro lado del hueco
            continue
        filas.append({
            "origen": fila["periodo"], "destino": _periodo(n_destino),
            "log_hoy": lp[n_origen],
            "cambio": lp[n_destino] - lp[n_origen],
            # sin dato del mes anterior, inercia = 0 (no se inventa un valor)
            "inercia": lp[n_origen] - lp[n_origen - 1] if n_origen - 1 in lp.index else 0.0,
            "oni": fila["oni"], "lluvia": fila["lluvia"],
            "estacional": lp[n_destino - 12] - lp[n_origen] if n_destino - 12 in lp.index else np.nan,
        })
    return pd.DataFrame(filas)


def _matriz(filas: pd.DataFrame) -> np.ndarray:
    """Variables del modelo: inercia, ONI, lluvia y un indicador por mes de destino."""
    mes = filas["destino"] % 100
    return np.column_stack([filas[["inercia", "oni", "lluvia"]].fillna(0).to_numpy(dtype=float)]
                           + [(mes == m).to_numpy(dtype=float) for m in MESES])


def _ajustar(entrenamiento: pd.DataFrame) -> np.ndarray:
    beta, *_ = np.linalg.lstsq(_matriz(entrenamiento), entrenamiento["cambio"].to_numpy(dtype=float), rcond=None)
    return beta


def backtest(serie: pd.DataFrame, horizonte: int) -> pd.DataFrame:
    """Simula pronosticar en vivo en cada uno de los ultimos ORIGENES_BACKTEST meses."""
    filas = armar_filas(serie, horizonte)
    salida = []
    for origen in sorted(filas["origen"])[-ORIGENES_BACKTEST:]:
        # Solo filas cuyo destino ya habia ocurrido en el mes de origen: nada del futuro
        entrenamiento = filas[filas["destino"] <= origen]
        if len(entrenamiento) < MINIMO_ENTRENAMIENTO:
            continue
        fila = filas[filas["origen"] == origen]
        prediccion = (_matriz(fila) @ _ajustar(entrenamiento)).item()
        salida.append({"origen": origen, "destino": int(fila["destino"].iloc[0]),
                       "real_log": float(fila["log_hoy"].iloc[0] + fila["cambio"].iloc[0]),
                       "pronostico_log": float(fila["log_hoy"].iloc[0]) + prediccion,
                       "sin_cambio_log": float(fila["log_hoy"].iloc[0]),
                       "estacional_log": float(fila["log_hoy"].iloc[0] + fila["estacional"].iloc[0])})
    return pd.DataFrame(salida)


def _mae(real: pd.Series, pred: pd.Series) -> float:
    """Error absoluto medio en % (diferencia de logaritmos x 100 ~ diferencia en %)."""
    error = (real - pred).dropna()
    return float(error.abs().mean() * 100) if len(error) >= 12 else np.inf


def evaluar(serie: pd.DataFrame, horizonte: int) -> dict:
    """Error del modelo y de los dos ingenuos en el backtest."""
    bt = backtest(serie, horizonte)
    return {"backtest": bt,
            "mae_modelo": _mae(bt["real_log"], bt["pronostico_log"]),
            "mae_sin_cambio": _mae(bt["real_log"], bt["sin_cambio_log"]),
            "mae_estacional": _mae(bt["real_log"], bt["estacional_log"])}


def pronosticar(serie: pd.DataFrame, horizontes=(1, 2, 3)) -> pd.DataFrame:
    """Pronostico desde el ultimo mes con dato, con banda del 80 % y el modelo elegido."""
    s = serie.set_index(_n(serie["periodo"]))
    n_hoy = int(s.index.max())
    hoy = s.loc[n_hoy]
    salida = []
    for h in horizontes:
        ev = evaluar(serie, h)
        bt = ev["backtest"]
        ingenuo = "sin_cambio" if ev["mae_sin_cambio"] <= ev["mae_estacional"] else "estacional"
        mae_ingenuo = ev[f"mae_{ingenuo}"]
        gana = ev["mae_modelo"] < MARGEN_PARA_GANAR * mae_ingenuo
        n_destino = n_hoy + h

        if gana:
            fila = pd.DataFrame([{"destino": _periodo(n_destino), "oni": hoy["oni"], "lluvia": hoy["lluvia"],
                                  "inercia": hoy["log_precio"] - s.loc[n_hoy - 1, "log_precio"]
                                  if n_hoy - 1 in s.index else 0.0}])
            centro = hoy["log_precio"] + (_matriz(fila) @ _ajustar(armar_filas(serie, h))).item()
            errores, modelo = bt["real_log"] - bt["pronostico_log"], "regresion"
        elif ingenuo == "estacional" and n_destino - 12 in s.index and n_hoy - 12 in s.index:
            centro = hoy["log_precio"] + s.loc[n_destino - 12, "log_precio"] - s.loc[n_hoy - 12, "log_precio"]
            errores, modelo = bt["real_log"] - bt["estacional_log"], "estacional"
        else:
            centro = hoy["log_precio"]
            errores, modelo = bt["real_log"] - bt["sin_cambio_log"], "sin_cambio"

        bajo, alto = np.nanpercentile(errores, [10, 90]) if errores.notna().any() else (0.0, 0.0)
        salida.append({"periodo": _periodo(n_destino), "horizonte": h, "valor": float(np.exp(centro)),
                       "lim_inf": float(np.exp(centro + min(bajo, 0))), "lim_sup": float(np.exp(centro + max(alto, 0))),
                       "modelo": modelo, "mae_modelo": ev["mae_modelo"], "mae_ingenuo": mae_ingenuo,
                       "gana_al_ingenuo": gana})
    return pd.DataFrame(salida)


def construir(con) -> pd.DataFrame:
    """Para cada producto (mediana nacional): historia real, backtest a 1 mes y pronostico."""
    precios = con.execute(
        "SELECT producto, periodo, median(precio_cop_kg) AS precio FROM fact_precio_mayorista "
        "WHERE mes_cerrado GROUP BY producto, periodo").df()
    precios["log_precio"] = np.log(precios["precio"])
    oni = con.execute("SELECT anio * 100 + mes AS periodo, anomalia AS oni FROM fact_enso").df()
    lluvia = con.execute(
        "SELECT p.producto_sipsa AS producto, c.periodo, avg(c.precipitacion_anomalia) AS lluvia "
        "FROM puente_zona_sipsa p JOIN fact_clima c "
        "ON c.producto = p.producto_zona AND c.departamento = p.departamento GROUP BY 1, 2").df()

    tablas = []
    for producto, serie in precios.groupby("producto"):
        serie = (serie.merge(oni, on="periodo", how="left")
                 .merge(lluvia[lluvia["producto"] == producto].drop(columns="producto"), on="periodo", how="left")
                 .sort_values("periodo"))
        futuro = pronosticar(serie).assign(tipo="pronostico")
        bt = backtest(serie, 1)
        prueba = pd.DataFrame({"periodo": bt["destino"], "horizonte": 1, "valor": np.exp(bt["pronostico_log"]),
                               "modelo": "regresion", "tipo": "prueba"})
        real = serie[["periodo", "precio"]].rename(columns={"precio": "valor"}).assign(tipo="real")
        # Las filas real y prueba llevan el veredicto del horizonte 1 (el del backtest
        # que muestran); cada fila de pronostico conserva el de SU horizonte.
        veredicto_h1 = futuro.iloc[0][["mae_modelo", "mae_ingenuo", "gana_al_ingenuo"]].to_dict()
        historia = pd.concat([real, prueba], ignore_index=True).assign(**veredicto_h1)
        tablas.append(pd.concat([historia, futuro], ignore_index=True)
                      .assign(producto=producto, mercado="nacional"))
    salida = pd.concat(tablas, ignore_index=True)
    columnas = ["producto", "mercado", "periodo", "horizonte", "tipo", "valor", "lim_inf", "lim_sup",
                "modelo", "mae_modelo", "mae_ingenuo", "gana_al_ingenuo"]
    return salida[columnas]
