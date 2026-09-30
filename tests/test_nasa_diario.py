"""Pruebas del clima diario de NASA POWER. Ninguna toca la red.

`nasa_power_diario_boyaca.json` es una respuesta real (Boyaca, 1 ago - 20 sep 2026)
recortada al encabezado y los datos. Los ultimos 3 dias llegan con -999.
"""

import copy
import json
from pathlib import Path

import pandas as pd

from src.acquisition.nasa_power_diario import MINIMO_DIAS, a_mensual
from src.cleaning.complementarias import unir_clima

FIXTURE = Path(__file__).parent / "fixtures" / "nasa_power_diario_boyaca.json"
ZONA = {"producto": "Papa", "departamento": "Boyaca", "lat": 5.54, "lon": -73.36}


def _respuesta() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _lluvia(filas, mes):
    return next(f for f in filas if f["parametro"] == "PRECTOTCORR" and f["mes"] == mes)


def test_agosto_es_el_promedio_de_sus_31_dias():
    agosto = _lluvia(a_mensual(_respuesta(), ZONA), 8)
    assert agosto["dias_con_dato"] == 31
    assert agosto["valor"] == 7.37


def test_los_menos_999_no_entran_al_promedio():
    """Del 18 al 20 de septiembre vienen en -999: se cuentan 17 dias, no 20."""
    septiembre = _lluvia(a_mensual(_respuesta(), ZONA), 9)
    assert septiembre["dias_con_dato"] == 17
    assert septiembre["valor"] == 7.4          # si entrara un -999 daria un numero negativo


def test_un_mes_con_pocos_dias_se_descarta():
    r = _respuesta()
    corta = copy.deepcopy(r)
    for par, serie in corta["properties"]["parameter"].items():
        corta["properties"]["parameter"][par] = {
            k: v for k, v in serie.items() if k.startswith("202608") or k < f"202609{MINIMO_DIAS:02d}"
        }
    meses = {f["mes"] for f in a_mensual(corta, ZONA)}
    assert meses == {8}


def test_unir_clima_no_duplica_y_gana_el_mensual():
    llave = {"producto": "Papa", "departamento": "Boyaca", "lat": 5.54, "lon": -73.36,
             "elevacion_grilla_m": 2557.41}
    mensual = pd.DataFrame([{**llave, "anio": 2025, "mes": 12, "PRECTOTCORR": 3.0, "T2M": 12.0}])
    diario = pd.DataFrame([
        {**llave, "anio": 2025, "mes": 12, "PRECTOTCORR": 9.9, "T2M": 9.9, "dias_con_dato": 31},
        {**llave, "anio": 2026, "mes": 1, "PRECTOTCORR": 2.0, "T2M": 13.0, "dias_con_dato": 31},
    ])
    unido = unir_clima(mensual, diario)
    assert len(unido) == 2
    dic = unido.set_index("mes")
    assert dic.loc[12, "PRECTOTCORR"] == 3.0 and dic.loc[12, "fuente"] == "mensual"
    assert dic.loc[1, "fuente"] == "diario"


def test_unir_clima_sin_diario_igual_trae_las_columnas():
    mensual = pd.DataFrame([{"producto": "Papa", "departamento": "Boyaca", "anio": 2025, "mes": 1,
                             "PRECTOTCORR": 3.0}])
    unido = unir_clima(mensual, pd.DataFrame())
    assert {"fuente", "dias_con_dato"} <= set(unido.columns)
