"""Pruebas del mapa, el clima y las fuentes que exporta la web.

Las dos ultimas leen la base real (solo lectura, sin red): lo que se prueba es
que lo exportado sea coherente con lo que hay en la base.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.exportar_web import MESES_DEL_MAPA, armar_clima, armar_fuentes, armar_mapa, simplificar
from src.common.rutas import BASE_DUCKDB


def test_simplificar_redondea_quita_repetidos_y_conserva_el_codigo():
    geojson = {"features": [{
        "properties": {"DPTO": "05", "NOMBRE_DPT": "ANTIOQUIA"},
        "geometry": {"type": "Polygon", "coordinates": [[
            [-75.001, 6.001], [-75.002, 6.002],       # los dos redondean al mismo punto
            [-74.5, 6.0], [-74.5, 6.5], [-75.001, 6.001],
        ]]},
    }]}
    rasgo = simplificar(geojson)["features"][0]
    assert rasgo["properties"] == {"codigo": "05"}        # el codigo va como texto, con su cero
    assert rasgo["geometry"]["type"] == "MultiPolygon"
    assert rasgo["geometry"]["coordinates"] == [[[[-75.0, 6.0], [-74.5, 6.0], [-74.5, 6.5], [-75.0, 6.0]]]]


def test_simplificar_descarta_un_anillo_que_queda_sin_area():
    """Una isla diminuta se vuelve un solo punto al redondear: no se dibuja."""
    geojson = {"features": [{
        "properties": {"DPTO": "88"},
        "geometry": {"type": "MultiPolygon", "coordinates": [
            [[[-81.7001, 12.5001], [-81.7002, 12.5002], [-81.7003, 12.5001], [-81.7001, 12.5001]]],
            [[[-81.0, 12.0], [-80.0, 12.0], [-80.0, 13.0], [-81.0, 12.0]]],
        ]},
    }]}
    assert len(simplificar(geojson)["features"][0]["geometry"]["coordinates"]) == 1


@pytest.fixture(scope="module")
def con():
    if not BASE_DUCKDB.exists():
        pytest.skip("la base no esta construida")
    conexion = duckdb.connect(str(BASE_DUCKDB), read_only=True)
    yield conexion
    conexion.close()


def test_el_mapa_trae_los_33_departamentos_y_declara_los_que_no_tienen_dato(con):
    precios = con.execute("SELECT * FROM col_precio_mayorista_mensual").df()
    mapa = armar_mapa(con, precios)

    assert len(mapa["periodos"]) == MESES_DEL_MAPA
    assert len(mapa["departamentos"]) == 33
    assert len({d["codigo"] for d in mapa["departamentos"]}) == 33
    for d in mapa["departamentos"]:
        # Sin mercado o sin sensores el dato va como None: nunca como cero.
        for capa in ("precio", "lluvia"):
            assert d[capa] is None or len(d[capa]) == MESES_DEL_MAPA
    con_precio = sum(d["precio"] is not None for d in mapa["departamentos"])
    assert con_precio == con.execute("SELECT count(DISTINCT dpto_codigo) FROM catalogo_mercado").fetchone()[0]
    # Cada estacion es un punto dentro de Colombia continental o sus islas.
    assert all(-82 < lon < -66 and -5 < lat < 14 for lon, lat in mapa["estaciones"])
    assert mapa["nino"]["fase"] in {"El Nino", "La Nina", "Neutral"}


def test_las_fuentes_van_separadas_y_los_huecos_son_coherentes(con):
    salida = armar_fuentes(con)
    origenes = [f["origen"] for f in salida["fuentes"]]
    assert set(origenes) == {"nacional", "internacional"}
    assert origenes.count("nacional") == 3
    assert all(f["filas"] > 0 and f["ultimo_dato"] for f in salida["fuentes"])

    h = salida["huecos"]
    assert h["departamentos_con_sensor"] <= h["departamentos_con_precio"] <= h["departamentos"]
    assert h["pronosticos_confiables"] <= h["productos"]
    assert h["relaciones_clima_firmes"] <= h["relaciones_clima"]
    assert h["meses_sin_precio"] == 13          # el hueco de SIPSA: 2021-01 a 2022-01


def test_la_cadena_del_clima_cuenta_lo_que_se_sostiene_sin_inflarlo(con):
    precios = con.execute("SELECT * FROM col_precio_mayorista_mensual").df()
    clima = armar_clima(con, precios)

    assert [e["eslabon"] for e in clima["cadena"]] == [
        "oni->lluvia", "lluvia->oferta", "oferta->precio", "lluvia->precio"]
    for e in clima["cadena"]:
        # Lo que se muestra como hallazgo tiene que salir de las pruebas que se sostienen.
        esperado = con.execute(
            "SELECT count(*), count(*) FILTER (WHERE q_valor < 0.1) FROM resultado_efecto_clima "
            "WHERE eslabon = ?", [e["eslabon"]]).fetchone()
        assert (e["pruebas"], e["firmes"]) == esperado
        assert len(e["hallazgos"]) <= e["firmes"]
    # Una pista nunca puede acertar mas veces de las que se probo.
    assert all(0 <= p["aciertos"] <= p["meses"] for p in clima["pistas"])
    assert all(p["senal"] in {"al alza", "a la baja", "sin dato"} for p in clima["pistas"])


def test_la_lluvia_esperada_no_trae_la_resta_contra_lo_normal(con):
    """Esa resta mezcla dos modelos y daba cifras imposibles: no se exporta."""
    precios = con.execute("SELECT * FROM col_precio_mayorista_mensual").df()
    mapa = armar_mapa(con, precios)
    con_pronostico = [d for d in mapa["departamentos"] if d["lluvia_esperada"]]
    assert con_pronostico
    for d in con_pronostico:
        for mes in d["lluvia_esperada"]:
            assert set(mes) == {"periodo", "seco", "central", "lluvioso"}
            assert mes["seco"] <= mes["central"] <= mes["lluvioso"]
