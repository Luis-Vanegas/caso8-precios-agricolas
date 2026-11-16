"""Pruebas del exportador de la web: lo que sale en el tablero tiene que ser cierto."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.exportar_web import NACIONAL, armar_tablero, nombre_mercado, nombre_mes, nombre_producto


def _precios() -> pd.DataFrame:
    """Dos mercados, 14 meses seguidos y un mes en curso (abierto) que no debe contar."""
    filas = []
    for i in range(14):
        periodo = 202501 + i if i < 12 else 202601 + i - 12
        for mercado, base in (("BOGOTÁ, D.C.", 1000.0), ("SAN JOSÉ DE CÚCUTA", 2000.0)):
            filas.append({"mercado": mercado, "producto": "Papa negra*", "periodo": periodo,
                          "anio": periodo // 100, "mes": periodo % 100,
                          "precio_cop_kg": base * (1 + 0.1 * (i % 3)), "mes_cerrado": True})
    filas.append({"mercado": "BOGOTÁ, D.C.", "producto": "Papa negra*", "periodo": 202603,
                  "anio": 2026, "mes": 3, "precio_cop_kg": 9999.0, "mes_cerrado": False})
    return pd.DataFrame(filas)


def _pronosticos() -> pd.DataFrame:
    return pd.DataFrame([
        {"producto": "Papa negra*", "tipo": "pronostico", "periodo": 202603 + h - 1, "horizonte": h,
         "valor": 1500.0, "lim_inf": 1200.0, "lim_sup": 1800.0, "modelo": "sin_cambio",
         "mae_modelo": 14.0, "mae_ingenuo": 12.0, "gana_al_ingenuo": False}
        for h in (1, 2, 3)])


@pytest.fixture
def tablero() -> dict:
    return armar_tablero(_precios(), _pronosticos())


def test_el_tablero_usa_el_ultimo_mes_cerrado_y_no_el_mes_en_curso(tablero):
    assert tablero["ultimo_mes"] == 202602
    assert all(f["precio"] != 9999 for f in tablero["filas"])


def test_hay_una_fila_por_mercado_mas_la_nacional(tablero):
    assert tablero["mercados"] == [NACIONAL, "Bogotá, D.C.", "San José de Cúcuta"]
    assert sorted(f["mercado"] for f in tablero["filas"]) == sorted(tablero["mercados"])


def test_el_cambio_frente_al_mes_pasado_sale_de_los_dos_ultimos_precios(tablero):
    fila = next(f for f in tablero["filas"] if f["mercado"] == "Bogotá, D.C.")
    anterior, actual = fila["serie"][-2], fila["serie"][-1]
    assert fila["precio"] == actual
    assert fila["cambio_mes_pct"] == pytest.approx((actual / anterior - 1) * 100, abs=0.1)


def test_el_cambio_frente_al_anio_pasado_compara_el_mismo_mes(tablero):
    fila = next(f for f in tablero["filas"] if f["mercado"] == "Bogotá, D.C.")
    hace_un_anio = fila["serie"][tablero["periodos"].index(202502)]
    assert fila["cambio_anio_pct"] == pytest.approx((fila["precio"] / hace_un_anio - 1) * 100, abs=0.1)


def test_solo_la_fila_nacional_lleva_pronostico_y_dice_si_es_confiable(tablero):
    nacional = next(f for f in tablero["filas"] if f["mercado"] == NACIONAL)
    assert [m["periodo"] for m in nacional["pronostico"]["meses"]] == [202603, 202604, 202605]
    assert nacional["pronostico"]["confiable"] is False
    assert all(f["pronostico"] is None for f in tablero["filas"] if f["mercado"] != NACIONAL)


def test_un_mes_sin_precio_va_vacio_y_no_inventado(tablero):
    fila = next(f for f in tablero["filas"] if f["mercado"] == NACIONAL)
    # La ventana pide 24 meses y solo hay 14: los 10 primeros no tienen dato.
    assert fila["serie"][:10] == [None] * 10
    assert None not in fila["serie"][10:]


def test_sin_historia_suficiente_el_semaforo_dice_sin_dato_y_no_verde(tablero):
    # Con dos meses de comparacion anual no hay historia para decir si es raro.
    assert {f["estado_anio"] for f in tablero["filas"]} == {"sin dato"}


def test_los_nombres_se_muestran_limpios():
    assert nombre_producto("Piña *") == "Piña"
    assert nombre_mercado("SAN JOSÉ DE CÚCUTA") == "San José de Cúcuta"
    assert nombre_mercado("BOGOTÁ, D.C.") == "Bogotá, D.C."
    assert nombre_mes(202609) == "septiembre de 2026"
