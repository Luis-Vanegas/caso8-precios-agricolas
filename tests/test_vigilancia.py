"""Pruebas de la lista de vigilancia. Datos construidos a mano para saber la respuesta."""

import numpy as np
import pandas as pd

from src.indicators import vigilancia as v

PUENTE = pd.DataFrame([{"producto_sipsa": "Tomate*", "producto_zona": "Tomate",
                        "departamento": "Norte de Santander"}])


def _periodos(desde: str, meses: int) -> list[int]:
    return [int(p.strftime("%Y%m")) for p in pd.period_range(desde, periods=meses, freq="M")]


def test_rezagar_cuenta_meses_de_calendario_y_cruza_el_anio():
    serie = pd.DataFrame({"periodo": [202011, 202012], "x": [1, 2]})
    assert list(v.rezagar(serie, 2)["periodo"]) == [202101, 202102]


def test_la_lluvia_de_hace_k_meses_se_toma_aunque_falten_precios_en_medio():
    """Con un hueco en los precios, el rezago tiene que seguir siendo de calendario.

    Precio de t = -lluvia de t-3 en todos los meses con precio. Si el rezago se
    hiciera corriendo filas (el error que tenia la exploracion), el hueco
    mezclaria meses y la correlacion no daria -1.
    """
    periodos = _periodos("2019-01", 60)
    rng = np.random.default_rng(0)
    lluvia = pd.DataFrame({"producto": "Tomate", "departamento": "Norte de Santander",
                           "anio": [p // 100 for p in periodos], "mes": [p % 100 for p in periodos],
                           "precipitacion_anomalia": rng.normal(size=60)})
    por_periodo = dict(zip(periodos, lluvia["precipitacion_anomalia"]))
    con_precio = [p for i, p in enumerate(periodos) if i >= 3 and not (20 <= i < 33)]  # hueco de 13 meses
    ret = pd.DataFrame({"producto": "Tomate*", "periodo": con_precio,
                        "retorno": [-por_periodo[int((pd.Period(str(p), "M") - 3).strftime("%Y%m"))]
                                    for p in con_precio]})
    corr = v.correlacion_lluvia(ret, lluvia, PUENTE, rezagos=(3,))
    assert corr.loc[0, "spearman"] == -1.0


def test_senal_multiplica_los_signos_y_descarta_el_rezago_cero():
    corr = pd.DataFrame([
        {"producto": "Tomate*", "departamento": "Norte de Santander", "variable": "precipitacion_anomalia",
         "rezago": 3, "n": 60, "spearman": -0.45},
        {"producto": "Tomate*", "departamento": "Norte de Santander", "variable": "precipitacion_anomalia",
         "rezago": 0, "n": 60, "spearman": 0.9},
    ])
    clima = pd.DataFrame([{"producto": "Tomate", "departamento": "Norte de Santander",
                           "anio": 2026, "mes": 6, "precipitacion_anomalia": -0.97}])
    s = v.senales(corr, clima, PUENTE, proximo_periodo=202609)
    assert len(s) == 1                                 # el rezago 0 no anticipa nada
    fila = s.iloc[0]
    assert fila["periodo_lluvia"] == 202606            # septiembre menos 3 meses
    assert fila["senal"] == "al alza"                  # (-) x (-) = presion al alza


def test_sin_lluvia_conocida_no_hay_senal():
    corr = pd.DataFrame([{"producto": "Tomate*", "departamento": "Norte de Santander",
                          "variable": "precipitacion_anomalia", "rezago": 3, "n": 60, "spearman": -0.45}])
    clima = pd.DataFrame(columns=["producto", "departamento", "anio", "mes", "precipitacion_anomalia"])
    assert v.senales(corr, clima, PUENTE, 202609).iloc[0]["senal"] == "sin dato"
