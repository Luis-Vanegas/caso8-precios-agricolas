"""Tests del pronostico de precios.

Datos sinteticos a proposito: una serie con temporada fuerte (el modelo DEBE
ganarle al ingenuo) y la prueba clave contra la fuga de informacion: cambiar el
futuro no puede cambiar lo que se pronostico en el pasado.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.indicators import pronostico

PERIODOS = [a * 100 + m for a in (2020, 2022, 2023, 2024, 2025, 2026) for m in range(1, 13)]


def _serie_con_temporada(semilla: int = 0) -> pd.DataFrame:
    """Precio que sube en enero-junio y baja en julio-diciembre, todos los anos."""
    rng = np.random.default_rng(semilla)
    mes = np.array(PERIODOS) % 100
    patron = 0.3 * np.sin((mes - 1) / 12 * 2 * np.pi)
    log_precio = 7 + patron + rng.normal(scale=0.01, size=len(PERIODOS))
    return pd.DataFrame({"periodo": PERIODOS, "log_precio": log_precio, "oni": 0.0, "lluvia": 0.0})


def test_filas_solo_con_horizontes_de_calendario_exactos():
    df = pronostico.armar_filas(_serie_con_temporada(), horizonte=1)
    # 202012 -> 202201 son 13 meses (hueco de 2021): esa fila no puede existir
    assert 202012 not in df["origen"].tolist()
    assert ((df["destino"] // 100 * 12 + df["destino"] % 100)
            - (df["origen"] // 100 * 12 + df["origen"] % 100)).eq(1).all()


def test_con_temporada_fuerte_el_modelo_le_gana_al_que_no_cambia():
    r = pronostico.evaluar(_serie_con_temporada(), horizonte=1)
    assert r["mae_modelo"] < r["mae_sin_cambio"]


def test_cambiar_el_futuro_no_cambia_los_pronosticos_del_pasado():
    original = _serie_con_temporada()
    alterada = original.copy()
    alterada.loc[alterada["periodo"] >= 202601, "log_precio"] += 5    # futuro absurdo
    a = pronostico.backtest(original, horizonte=1)
    b = pronostico.backtest(alterada, horizonte=1)
    # Los pronosticos hechos ANTES de 2026 tienen que ser identicos
    antes = lambda d: d[d["destino"] < 202601].set_index("destino")["pronostico_log"]
    pd.testing.assert_series_equal(antes(a), antes(b))


def test_pronostico_futuro_con_banda_ordenada():
    p = pronostico.pronosticar(_serie_con_temporada(), horizontes=(1, 2, 3))
    assert p["periodo"].tolist() == [202701, 202702, 202703]
    assert ((p["lim_inf"] <= p["valor"]) & (p["valor"] <= p["lim_sup"])).all()


def test_si_no_le_gana_al_ingenuo_se_presenta_el_ingenuo():
    # Ruido puro: ningun modelo deberia ganarle de forma confiable al "no cambia"
    rng = np.random.default_rng(3)
    serie = pd.DataFrame({"periodo": PERIODOS, "oni": 0.0, "lluvia": 0.0,
                          "log_precio": 7 + np.cumsum(rng.normal(scale=0.05, size=len(PERIODOS)))})
    p = pronostico.pronosticar(serie, horizontes=(1,))
    fila = p.iloc[0]
    if not fila["gana_al_ingenuo"]:
        assert fila["modelo"] != "regresion"


def test_cada_horizonte_conserva_su_propio_veredicto():
    # Bug real del 2026-10-09: en `construir`, el veredicto del horizonte 1 pisaba
    # al de los horizontes 2 y 3. Se arma una base minima y se corre construir.
    import duckdb
    serie = _serie_con_temporada()
    con = duckdb.connect(":memory:")
    precios = serie.assign(mercado="BOGOTA", producto="Papa", precio_cop_kg=np.exp(serie["log_precio"]),
                           mes_cerrado=True)
    con.register("p", precios)
    con.execute("CREATE TABLE fact_precio_mayorista AS SELECT * FROM p")
    con.execute("CREATE TABLE fact_enso AS SELECT 2020 AS anio, 1 AS mes, 0.0 AS anomalia")
    con.execute("CREATE TABLE puente_zona_sipsa AS SELECT 'x' AS producto_sipsa, 'x' AS producto_zona, 'x' AS departamento")
    con.execute("CREATE TABLE fact_clima AS SELECT 'x' AS producto, 'x' AS departamento, 202001 AS periodo, 0.0 AS precipitacion_anomalia")

    tabla = pronostico.construir(con)
    futuro = tabla[tabla["tipo"] == "pronostico"].sort_values("horizonte")
    esperado = [pronostico.evaluar(serie.assign(oni=np.nan, lluvia=np.nan), h)["mae_modelo"] for h in (1, 2, 3)]
    assert futuro["mae_modelo"].round(6).tolist() == [round(e, 6) for e in esperado]
