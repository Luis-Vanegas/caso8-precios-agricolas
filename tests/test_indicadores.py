"""Tests de los indicadores de volatilidad y del modelo integrado.

Un indicador mal calculado no falla: devuelve un numero plausible. Por eso cada
test compara contra un valor calculado a mano, no contra "algo razonable".
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.indicators.volatilidad import (
    MINIMO_OBSERVACIONES,
    UMBRAL_AMARILLA,
    alertas,
    dependencia_importaciones,
    retornos,
    volatilidad,
)


def _serie(precios: list[float], periodos: list[int] | None = None) -> pd.DataFrame:
    periodos = periodos or [202001 + i for i in range(len(precios))]
    return pd.DataFrame(
        {
            "mercado": ["BOGOTA"] * len(precios),
            "producto": ["Papa"] * len(precios),
            "periodo": periodos,
            "precio_cop_kg": precios,
        }
    )


# --- Retornos ---------------------------------------------------------------

def test_retorno_logaritmico_se_calcula_bien():
    r = retornos(_serie([100.0, 200.0]))
    assert r["retorno_log"].iloc[1] == np.log(2)


def test_el_primer_periodo_no_tiene_retorno():
    r = retornos(_serie([100.0, 200.0]))
    assert pd.isna(r["retorno_log"].iloc[0])


def test_el_logaritmo_es_simetrico():
    """Subir al doble y volver a la mitad se cancela exactamente.

    Con variacion porcentual (+100% y -50%) no se cancela, y eso sesga
    cualquier promedio posterior. Por eso se usa logaritmo.
    """
    r = retornos(_serie([100.0, 200.0, 100.0]))
    assert r["retorno_log"].iloc[1] + r["retorno_log"].iloc[2] == 0


def test_un_hueco_en_la_serie_corta_el_retorno():
    """El salto de enero a junio no es comparable con un cambio mes a mes."""
    r = retornos(_serie([100.0, 200.0], periodos=[202001, 202006]))
    assert pd.isna(r["retorno_log"].iloc[1])


def test_el_cambio_de_anio_no_rompe_la_continuidad():
    r = retornos(_serie([100.0, 200.0], periodos=[202012, 202101]))
    assert r["retorno_log"].iloc[1] == np.log(2)


def test_un_precio_cero_no_produce_infinito():
    r = retornos(_serie([0.0, 100.0]))
    assert pd.isna(r["retorno_log"].iloc[1])


# --- Volatilidad ------------------------------------------------------------

def test_no_hay_volatilidad_sin_observaciones_suficientes():
    """Con pocos datos la desviacion estandar es ruido con cara de indicador."""
    v = volatilidad(_serie([100.0 * (1.01**i) for i in range(4)]))
    assert v["volatilidad"].isna().all()


def test_la_volatilidad_aparece_al_alcanzar_el_minimo():
    precios = [100.0 * (1.05 if i % 2 else 0.95) ** i for i in range(MINIMO_OBSERVACIONES + 3)]
    v = volatilidad(_serie(precios))
    assert v["volatilidad"].notna().any()


def test_una_serie_constante_tiene_volatilidad_cero():
    v = volatilidad(_serie([100.0] * 10))
    assert v["volatilidad"].dropna().eq(0).all()


def test_la_anualizacion_multiplica_por_raiz_de_doce():
    v = volatilidad(_serie([100.0 * (1.1 if i % 3 else 0.9) ** i for i in range(12)]))
    fila = v[v["volatilidad"].notna()].iloc[0]
    assert np.isclose(fila["volatilidad_anualizada"], fila["volatilidad"] * np.sqrt(12))


# --- Alertas ----------------------------------------------------------------

def test_una_serie_estable_no_enciende_alertas():
    a = alertas(_serie([100.0 + i for i in range(24)]))
    assert not a["alerta"].isin(["roja", "amarilla"]).any()


def test_un_salto_grande_enciende_alerta():
    precios = [100.0 + i * 0.5 for i in range(24)] + [400.0]
    a = alertas(_serie(precios))
    assert a["alerta"].iloc[-1] in ("amarilla", "roja")


def test_sin_z_score_no_se_afirma_que_esta_verde():
    """Decir 'verde' sin datos suficientes seria afirmar algo que no se sabe."""
    a = alertas(_serie([100.0, 110.0, 120.0]))
    assert a["alerta"].isna().all()


def test_el_z_score_no_mira_el_futuro():
    """expanding() usa solo pasado y presente.

    Si usara la media de toda la serie, el indicador de un mes dependeria de
    datos que en ese momento no existian, y la alerta seria inutil en vivo.
    """
    base = [100.0 + i for i in range(20)]
    corta = alertas(_serie(base))
    larga = alertas(_serie(base + [100.0, 5000.0, 100.0]))
    # El z-score del mes 20 no puede cambiar porque despues pasen cosas.
    assert np.isclose(
        corta["z_score"].iloc[19], larga["z_score"].iloc[19], equal_nan=True
    )


def test_la_direccion_distingue_alza_de_baja():
    a = alertas(_serie([100.0, 200.0, 100.0] + [100.0] * 10))
    assert a["direccion"].iloc[1] == "alza"
    assert a["direccion"].iloc[2] == "baja"


# --- Dependencia de importaciones -------------------------------------------

def _fao(filas) -> pd.DataFrame:
    return pd.DataFrame(filas, columns=["item_codigo", "elemento", "anio", "unidad", "valor"])


def test_dependencia_aplica_la_formula():
    """100 producidas + 50 importadas - 30 exportadas = 120; 50/120 = 41.67%."""
    d = dependencia_importaciones(
        _fao([
            (1, "Import quantity", 2020, "t", 50.0),
            (1, "Export quantity", 2020, "t", 30.0),
        ]),
        _fao([(1, "Production", 2020, "t", 100.0)]),
    )
    assert d.iloc[0]["consumo_aparente"] == 120.0
    assert np.isclose(d.iloc[0]["dependencia_pct"], 41.67, atol=0.01)


def test_consumo_aparente_no_positivo_no_da_porcentaje():
    """Exportar mas de lo disponible daria un porcentaje negativo sin sentido."""
    d = dependencia_importaciones(
        _fao([
            (1, "Import quantity", 2020, "t", 10.0),
            (1, "Export quantity", 2020, "t", 500.0),
        ]),
        _fao([(1, "Production", 2020, "t", 100.0)]),
    )
    assert pd.isna(d.iloc[0]["dependencia_pct"])


def test_dependencia_ignora_unidades_que_no_son_toneladas():
    d = dependencia_importaciones(
        _fao([
            (1, "Import quantity", 2020, "An", 9999.0),
            (1, "Import quantity", 2020, "t", 50.0),
        ]),
        _fao([(1, "Production", 2020, "t", 100.0)]),
    )
    assert d.iloc[0]["importacion"] == 50.0
