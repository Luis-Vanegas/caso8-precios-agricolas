"""Pruebas del sensor IDEAM. Ninguna toca la red.

`ideam_muestra.json` es un recorte real de s54a-sgyg (consultado el 2026-09-22).
Los agregados mensuales se arman a mano con las columnas que devuelve la
consulta SoQL, porque esa consulta todavia esta pendiente de verificar en vivo.
"""

import json
from pathlib import Path

import pandas as pd
import pytest

from src.acquisition import ideam
from src.cleaning.ideam import a_departamento, a_vocabulario_config, limpiar, sin_tilde

FIXTURES = Path(__file__).parent / "fixtures"
COLUMNAS_REALES = {
    "codigoestacion", "codigosensor", "fechaobservacion", "valorobservado",
    "nombreestacion", "departamento", "municipio", "zonahidrografica",
    "latitud", "longitud", "descripcionsensor", "unidadmedida",
}


def _fila(estacion, mes, n, suma="60", variable="precipitacion", minimo="0", maximo="4",
          promedio="0.05", depto="Boyacá"):
    return dict(codigoestacion=estacion, codigosensor="0240", nombreestacion=estacion,
                departamento=depto, municipio="Tunja", latitud="5.5", longitud="-73.3",
                mes=f"2025-{mes:02d}-01T00:00:00.000", suma=suma, promedio=promedio,
                minimo=minimo, maximo=maximo, n_lecturas=str(n), variable=variable)


def test_muestra_real_tiene_las_columnas_verificadas():
    filas = json.loads((FIXTURES / "ideam_muestra.json").read_text(encoding="utf-8"))
    assert all(set(f) == COLUMNAS_REALES for f in filas)
    assert {f["unidadmedida"] for f in filas} == {"mm"}


def test_todo_departamento_de_config_tiene_nombre_ideam():
    # Un nombre faltante no da error: da cero filas. Por eso se prueba.
    faltantes = [d for d in ideam.departamentos() if d not in ideam.NOMBRE_IDEAM]
    assert faltantes == []


def test_consulta_separa_sensores_y_acota_el_mes():
    # La consulta pide UN mes por llamada (el anio completo da timeout en Socrata).
    q = ideam.consulta_mensual("Boyacá", 2024, 3)
    assert "codigosensor" in q["$group"]
    assert "departamento = 'Boyacá'" in q["$where"]
    assert "'2024-03-01T00:00:00'" in q["$where"] and "< '2024-04-01T00:00:00'" in q["$where"]
    assert "sum(valorobservado)" in q["$select"]


def test_consulta_de_diciembre_cierra_en_enero_del_anio_siguiente():
    q = ideam.consulta_mensual("Boyacá", 2024, 12)
    assert "'2024-12-01T00:00:00'" in q["$where"] and "< '2025-01-01T00:00:00'" in q["$where"]


def test_sin_tilde():
    assert sin_tilde("Boyacá") == "Boyaca"
    assert sin_tilde("Quindío") == "Quindio"


def test_mes_incompleto_queda_invalido():
    df = limpiar(pd.DataFrame([_fila("A", 1, 4000), _fila("A", 2, 1000), _fila("A", 3, 4100)]))
    feb = df[df["mes"] == 2].iloc[0]
    assert feb["completitud"] == pytest.approx(0.25)
    assert not feb["valido"]
    assert df[df["mes"] != 2]["valido"].all()


def test_lluvia_negativa_y_temperatura_imposible_se_marcan():
    df = limpiar(pd.DataFrame([
        _fila("A", 1, 4000, minimo="-2"),
        _fila("T", 1, 700, variable="temperatura", promedio="18", minimo="9", maximo="60"),
    ]))
    assert df["fuera_de_rango"].all()
    assert not df["valido"].any()


def test_valor_es_suma_para_lluvia_y_promedio_para_temperatura():
    df = limpiar(pd.DataFrame([
        _fila("A", 1, 4000, suma="80"),
        _fila("T", 1, 700, variable="temperatura", suma="12600", promedio="18"),
    ]))
    assert df.set_index("variable").loc["precipitacion", "valor"] == 80
    assert df.set_index("variable").loc["temperatura", "valor"] == 18


def test_departamento_usa_mediana_de_validas_y_llave_sin_tilde():
    df = limpiar(pd.DataFrame([
        _fila("A", 1, 4000, suma="50"),
        _fila("B", 1, 4000, suma="70"),
        _fila("C", 1, 4000, suma="900", minimo="-1"),  # sensor dañado: se excluye
    ]))
    depto = a_departamento(df)
    fila = depto.iloc[0]
    assert fila["departamento"] == "Boyaca"
    assert fila["valor"] == 60
    assert fila["n_estaciones"] == 2


def test_las_dos_convenciones_de_mayusculas_quedan_en_un_solo_departamento():
    # IDEAM publica "BOYACÁ" (ene-jul) y "Boyacá" (ago-sep) para la misma red de estaciones.
    assert a_vocabulario_config("BOYACÁ") == a_vocabulario_config("Boyacá") == "Boyaca"
    assert a_vocabulario_config("NORTE DE SANTANDER") == "Norte de Santander"
    assert a_vocabulario_config("Norte De Santander") == "Norte de Santander"
    df = limpiar(pd.DataFrame([_fila("A", 1, 4000, depto="BOYACÁ"), _fila("A", 8, 4000, depto="Boyacá")]))
    assert set(df["departamento"]) == {"Boyaca"}
