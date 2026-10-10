"""Tests de la sensibilidad al clima (clima -> oferta -> precio).

Los datos son sinteticos A PROPOSITO: se fabrica una relacion conocida (por
ejemplo "el precio baja 0,5 % por cada 1 % mas de toneladas") y se comprueba que
el metodo la recupera. Si el metodo no encuentra un efecto que sabemos que esta,
tampoco hay que creerle cuando lo encuentre en los datos reales.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.indicators import sensibilidad

PERIODOS = [a * 100 + m for a in (2022, 2023, 2024, 2025) for m in range(1, 13)]


def test_ols_recupera_una_pendiente_conocida_con_estacionalidad():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({"periodo": PERIODOS})
    df["mes"] = df["periodo"] % 100
    df["x"] = rng.normal(size=len(df))
    # y = 2x + un efecto distinto para cada mes del ano + ruido pequeno
    df["y"] = 2 * df["x"] + df["mes"] * 0.3 + rng.normal(scale=0.05, size=len(df))
    r = sensibilidad.ols(df["y"], df[["x"]], efectos={"mes": df["mes"]})
    assert r["coeficiente"] == pytest.approx(2, abs=0.05)
    assert r["p_valor"] < 0.001
    assert r["n"] == 48


def test_ols_sin_relacion_no_es_significativa():
    rng = np.random.default_rng(1)
    x, y = rng.normal(size=48), rng.normal(size=48)
    r = sensibilidad.ols(pd.Series(y), pd.DataFrame({"x": x}))
    assert r["p_valor"] > 0.05


def test_q_valores_benjamini_hochberg():
    # Ejemplo de manual: 4 pruebas
    q = sensibilidad.q_valores(pd.Series([0.01, 0.04, 0.03, 0.005]))
    assert q.round(3).tolist() == [0.02, 0.04, 0.04, 0.02]


def test_cambio_log_no_cruza_huecos():
    df = pd.DataFrame({"serie": "a", "periodo": [202012, 202101, 202203, 202204],
                       "valor": [100.0, 110.0, 120.0, 132.0]})
    c = sensibilidad.cambio_log(df, ["serie"], "valor")
    # 202101 vs 202012 si (meses seguidos); 202203 vs 202101 no (hueco de 2021)
    assert np.isnan(c.loc[c["periodo"] == 202203, "cambio"].item())
    assert c.loc[c["periodo"] == 202204, "cambio"].item() == pytest.approx(np.log(1.1))


def test_mapa_articulos_solo_une_nombres_exactos():
    productos = pd.Series(["Papa negra*", "Yuca*", "Limón Común", "Tomate*", "Papa criolla"])
    articulos = pd.DataFrame({"art_id": [432, 76, 148, 541, 157],
                              "articulo": ["Yuca", "Limón común", "Tomate de árbol", "Papa criolla", "Papa capira"]})
    mapa = sensibilidad.mapa_articulos(productos, articulos)
    assert dict(zip(mapa["producto"], mapa["art_id"])) == {"Yuca*": 432, "Limón Común": 76, "Papa criolla": 541}
    # Papa negra* agrupa variedades y Tomate* no es Tomate de arbol: no se unen


def test_oferta_precio_panel_recupera_la_elasticidad():
    rng = np.random.default_rng(2)
    filas = []
    for dpto, efecto in (("11", 0.02), ("05", -0.01), ("76", 0.0)):
        ton = 1000 * np.exp(np.cumsum(rng.normal(scale=0.1, size=len(PERIODOS))))
        cambio_ton = np.diff(np.log(ton), prepend=np.nan)
        # el precio baja 0,5 % por cada 1 % mas de toneladas, mas un efecto del departamento
        cambio_precio = -0.5 * cambio_ton + efecto + rng.normal(scale=0.005, size=len(PERIODOS))
        precio = 2000 * np.exp(np.nancumsum(cambio_precio))
        for p, t, pr in zip(PERIODOS, ton, precio):
            filas.append({"dpto_codigo": dpto, "periodo": p, "toneladas": t, "precio": pr})
    df = pd.DataFrame(filas)
    r = sensibilidad.oferta_precio_panel(df)
    assert r["coeficiente"] == pytest.approx(-0.5, abs=0.05)
    assert r["p_valor"] < 0.001


def test_rezago_es_en_meses_de_calendario():
    # La lluvia de hace 1 mes para 202203 es la de 202202, aunque no haya precio en 202202
    lluvia = pd.DataFrame({"periodo": [202201, 202202, 202203], "x": [1.0, 2.0, 3.0]})
    movida = sensibilidad.rezagar(lluvia, 1)
    assert movida.set_index("periodo").loc[202203, "x"] == 2.0
