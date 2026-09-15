"""Tests del modelo estrella y sus chequeos de integridad.

Se construye una base en memoria con datos minimos y se comprueba que cada
chequeo detecte el problema que dice detectar. Un chequeo que nunca falla no
sirve de nada, asi que cada uno se prueba con el caso roto.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.integration.verificacion import CHEQUEOS, correr_chequeos


@pytest.fixture
def base() -> duckdb.DuckDBPyConnection:
    """Modelo minimo y consistente: todos los chequeos deben pasar."""
    con = duckdb.connect(":memory:")
    con.execute("CREATE TABLE dim_mercado AS SELECT 'BOGOTA' AS mercado, 1 AS series")
    con.execute(
        "CREATE TABLE dim_producto_sipsa AS "
        "SELECT 'Papa negra*' AS producto, 1 AS producto_codigo, 116 AS item_codigo_fao, "
        "'Potatoes' AS item_fao, 'agregada' AS tipo_correspondencia"
    )
    con.execute("CREATE TABLE dim_tiempo AS SELECT 2026 AS anio, 1 AS mes, 202601 AS periodo")
    con.execute(
        "CREATE TABLE dim_item_fao AS SELECT 116 AS item_codigo, 'Potatoes' AS item, "
        "'01510' AS item_cpc, true AS tiene_precio_productor, true AS tiene_produccion, "
        "true AS tiene_comercio"
    )
    con.execute(
        "CREATE TABLE dim_zona_productora AS SELECT 'Papa' AS producto, 'Boyaca' AS departamento, "
        "5.54 AS lat, -73.36 AS lon, 2557.4 AS elevacion_grilla_m"
    )
    con.execute(
        "CREATE TABLE puente_producto AS SELECT 'Papa negra*' AS producto_sipsa, "
        "116 AS item_codigo_fao, 'Potatoes' AS item_fao, 'agregada' AS tipo_correspondencia, "
        "false AS permite_comparar_precio"
    )
    con.execute(
        "CREATE TABLE puente_zona_sipsa AS SELECT 'Papa negra*' AS producto_sipsa, "
        "'Papa' AS producto_zona, 'Boyaca' AS departamento"
    )
    con.execute(
        "CREATE TABLE fact_precio_mayorista AS SELECT 'BOGOTA' AS mercado, "
        "'Papa negra*' AS producto, 2026 AS anio, 1 AS mes, 202601 AS periodo, "
        "2000.0 AS precio_cop_kg, 1800.0 AS precio_min, 2200.0 AS precio_max, "
        "20 AS dias_con_dato, 116 AS item_codigo_fao, 'agregada' AS tipo_correspondencia, "
        "false AS imputado"
    )
    con.execute(
        "CREATE TABLE fact_precio_productor AS SELECT 116 AS item_codigo, 5530 AS elemento_codigo, "
        "'Producer Price' AS elemento, 'LCU' AS unidad, 2026 AS anio, NULL::INTEGER AS mes, "
        "'anual' AS frecuencia, 2000000.0 AS valor, 'A' AS flag, false AS imputado"
    )
    for tabla in ("fact_produccion", "fact_comercio"):
        con.execute(
            f"CREATE TABLE {tabla} AS SELECT 116 AS item_codigo, 5510 AS elemento_codigo, "
            "'Production' AS elemento, 't' AS unidad, 2026 AS anio, 100.0 AS valor, "
            "'A' AS flag, false AS imputado"
        )
    con.execute(
        "CREATE TABLE fact_clima AS SELECT 'Papa' AS producto, 'Boyaca' AS departamento, "
        "2026 AS anio, 1 AS mes, 202601 AS periodo, 3.0 AS precipitacion_mm_dia, "
        "13.0 AS temperatura_c, 0.5 AS precipitacion_anomalia"
    )
    con.execute(
        # El tipo va explicito: sin el cast DuckDB infiere DECIMAL(2,1) del 1.8
        # y el test que prueba un valor fuera de rango no podria escribirlo.
        "CREATE TABLE fact_enso AS SELECT 2026 AS anio, 'DJF' AS trimestre, 1 AS mes, "
        "1.8::DOUBLE AS anomalia, 'El Nino' AS fase, true AS provisional"
    )
    return con


def test_el_modelo_consistente_pasa_todos_los_chequeos(base):
    resultados = correr_chequeos(base)
    fallidos = {n: r.detalle for n, r in resultados.items() if not r.ok}
    assert not fallidos, fallidos


def test_se_corren_todos_los_chequeos_declarados(base):
    assert set(correr_chequeos(base)) == set(CHEQUEOS)


def test_detecta_un_hecho_que_apunta_a_un_mercado_inexistente(base):
    base.execute("UPDATE fact_precio_mayorista SET mercado = 'ATLANTIS'")
    assert not correr_chequeos(base)["mayorista_sin_mercado"].ok


def test_detecta_una_clave_duplicada(base):
    base.execute("INSERT INTO fact_precio_mayorista SELECT * FROM fact_precio_mayorista")
    assert not correr_chequeos(base)["mayorista_clave_duplicada"].ok


def test_detecta_un_precio_no_positivo(base):
    base.execute("UPDATE fact_precio_mayorista SET precio_cop_kg = 0")
    assert not correr_chequeos(base)["precio_mayorista_no_positivo"].ok


def test_detecta_el_rango_de_precio_invertido(base):
    base.execute("UPDATE fact_precio_mayorista SET precio_min = 9999")
    assert not correr_chequeos(base)["rango_de_precio_invertido"].ok


def test_detecta_que_el_puente_marque_comparable_algo_que_no_lo_es(base):
    """Si una correspondencia agregada se cuela como comparable, los margenes son falsos."""
    base.execute("UPDATE puente_producto SET permite_comparar_precio = true")
    assert not correr_chequeos(base)["puente_marca_comparable_lo_que_no_es"].ok


def test_detecta_el_puente_de_zona_con_nombre_generico(base):
    """El error real: la config decia 'Papa' y SIPSA dice 'Papa negra*'.

    El join corria sin error y unia cero filas.
    """
    base.execute("UPDATE puente_zona_sipsa SET producto_sipsa = 'Papa'")
    resultados = correr_chequeos(base)
    assert not resultados["puente_zona_nombra_producto_inexistente"].ok
    assert not resultados["el_cruce_clima_sipsa_no_une_nada"].ok


def test_detecta_que_el_cruce_de_clima_quede_vacio(base):
    """Aunque los nombres sean validos, si no hay solape de periodos no une nada."""
    base.execute("UPDATE fact_clima SET anio = 1999")
    assert not correr_chequeos(base)["el_cruce_clima_sipsa_no_une_nada"].ok


def test_detecta_una_anomalia_enso_fisicamente_imposible(base):
    base.execute("UPDATE fact_enso SET anomalia = 40")
    assert not correr_chequeos(base)["enso_fuera_de_rango"].ok


def test_un_chequeo_con_sql_roto_se_reporta_como_falla(base):
    base.execute("DROP TABLE fact_enso")
    resultado = correr_chequeos(base)["enso_fuera_de_rango"]
    assert not resultado.ok
    assert "fallo" in resultado.detalle
