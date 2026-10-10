"""Tests de los quiebres estructurales (Chow y Brown-Forsythe).

Datos sinteticos a proposito: se fabrica una serie CON cambio y otra SIN cambio,
y se comprueba que cada prueba distingue las dos.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.indicators import quiebres

# Meses con precio: 2020, hueco en 2021 (como SIPSA), 2022 a 2026
PERIODOS = [a * 100 + m for a in (2020, 2022, 2023, 2024, 2025, 2026) for m in range(1, 13)]


def test_chow_detecta_un_cambio_de_ritmo():
    rng = np.random.default_rng(0)
    antes = pd.Series(rng.normal(0.00, 0.02, 40))
    despues = pd.Series(rng.normal(0.05, 0.02, 40))    # empieza a subir 5 % por mes
    assert quiebres.chow_media(antes, despues)["p_valor"] < 0.001


def test_chow_no_ve_cambio_en_ruido_puro():
    rng = np.random.default_rng(1)
    serie = rng.normal(0, 0.05, 80)
    assert quiebres.chow_media(pd.Series(serie[:40]), pd.Series(serie[40:]))["p_valor"] > 0.05


def test_brown_forsythe_detecta_que_aumento_la_volatilidad():
    rng = np.random.default_rng(2)
    antes, despues = pd.Series(rng.normal(0, 0.02, 40)), pd.Series(rng.normal(0, 0.10, 40))
    r = quiebres.brown_forsythe(antes, despues)
    assert r["p_valor"] < 0.001
    assert r["valor_despues"] > r["valor_antes"]


def test_precio_relativo_quita_la_inflacion_comun():
    # Dos productos que suben exactamente igual: frente a la canasta no cambian
    df = pd.DataFrame({"producto": ["a"] * 3 + ["b"] * 3, "periodo": [202201, 202202, 202203] * 2,
                       "precio": [100, 110, 121, 50, 55, 60.5]})
    rel = quiebres.precio_relativo(df)
    rango = rel.groupby("producto")["relativo"].agg(lambda s: s.max() - s.min())
    assert (rango < 1e-9).all()    # constante salvo decimales de punto flotante


def test_candidatos_solo_con_meses_suficientes_a_cada_lado():
    enso = pd.DataFrame({"periodo": [202302, 202306, 202405, 202510], "fase": ["Neutral", "El Nino", "Neutral", "La Nina"]})
    c = quiebres.candidatos(enso, pd.Series(PERIODOS), minimo=18)
    # 202510 deja menos de 18 meses despues (hasta 202612 hay 15)
    assert c["periodo"].tolist() == [202302, 202306, 202405]


def test_inicios_de_fase_marca_solo_los_cambios():
    enso = pd.DataFrame({"anio": [2023] * 4, "mes": [4, 5, 6, 7], "fase": ["Neutral", "Neutral", "El Nino", "El Nino"]})
    assert quiebres.inicios_de_fase(enso, desde=202305)["periodo"].tolist() == [202306]
