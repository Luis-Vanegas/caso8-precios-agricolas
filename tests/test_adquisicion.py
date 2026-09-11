"""Tests de los parsers de adquisicion. Ninguno toca la red.

Las fixtures son recortes de respuestas reales guardadas en Fase 0, no ejemplos
inventados: si la fuente cambia de formato, estos tests son los que avisan.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import faostat_bulk, nasa_power, oni, pink_sheet, sipsa
from src.common.modelos import ResultadoDescarga
from src.common.registro import conectar, registrar, ultima_actualizacion_fuente

FIXTURES = Path(__file__).parent / "fixtures"


# --- FAOSTAT bulk -----------------------------------------------------------

def test_catalogo_extrae_solo_dominios_del_caso():
    datasets = faostat_bulk.leer_catalogo((FIXTURES / "faostat_catalogo.xml").read_bytes())
    assert set(datasets) == {"PP", "PE"}


def test_catalogo_toma_la_version_normalizada():
    datasets = faostat_bulk.leer_catalogo((FIXTURES / "faostat_catalogo.xml").read_bytes())
    for info in datasets.values():
        assert "(Normalized)" in info["url"]


def test_catalogo_parsea_la_fecha_de_actualizacion():
    datasets = faostat_bulk.leer_catalogo((FIXTURES / "faostat_catalogo.xml").read_bytes())
    assert datasets["PP"]["actualizado"] == datetime(2026, 1, 9)
    assert datasets["PP"]["filas"] == 1319563


def test_catalogo_no_explota_con_fecha_invalida():
    xml = b"""<Datasets><Dataset>
        <DatasetCode>PP</DatasetCode>
        <DateUpdate>ayer</DateUpdate>
        <FileLocation>https://x/Prices_E_All_Data_(Normalized).zip</FileLocation>
    </Dataset></Datasets>"""
    assert faostat_bulk.leer_catalogo(xml)["PP"]["actualizado"] is None


# --- SIPSA ------------------------------------------------------------------

def test_sipsa_parsea_los_campos_reales():
    registros = sipsa.leer_registros(FIXTURES / "sipsa_promedios.xml")
    assert len(registros) == 3
    assert set(registros[0]) == {
        "ciudad", "codProducto", "enviado", "fechaCaptura",
        "fechaCreacion", "precioPromedio", "producto", "regId",
    }


def test_sipsa_ultima_captura_es_la_mayor():
    registros = [
        {"fechaCaptura": "2026-09-08T00:00:00-05:00"},
        {"fechaCaptura": "2026-09-10T00:00:00-05:00"},
        {"fechaCaptura": "2026-09-09T00:00:00-05:00"},
    ]
    assert sipsa._ultima_captura(registros) == "2026-09-10"


def test_sipsa_rechaza_metodo_desconocido():
    with pytest.raises(ValueError):
        sipsa.invocar("borrarTodo", Path("/tmp/x.xml"))


# --- ONI --------------------------------------------------------------------

def test_oni_clasifica_las_tres_fases():
    assert oni.clasificar(1.8) == "El Nino"
    assert oni.clasificar(-0.7) == "La Nina"
    assert oni.clasificar(0.2) == "Neutral"


def test_oni_los_umbrales_son_inclusivos():
    assert oni.clasificar(0.5) == "El Nino"
    assert oni.clasificar(-0.5) == "La Nina"


def test_oni_lee_el_archivo_real_y_descarta_el_encabezado():
    filas = oni.leer((FIXTURES / "oni.txt").read_text(encoding="utf-8"))
    assert filas
    assert all(isinstance(f["anio"], int) for f in filas)
    assert filas[0]["trimestre"] == "DJF"
    assert filas[0]["mes_central"] == 1


def test_oni_marca_provisionales_solo_los_ultimos():
    filas = oni.leer((FIXTURES / "oni.txt").read_text(encoding="utf-8"))
    assert [f["provisional"] for f in filas[-2:]] == [True, True]
    assert not any(f["provisional"] for f in filas[:-2])


# --- NASA POWER -------------------------------------------------------------

def _respuesta(valores: dict, fill=-999.0) -> dict:
    return {"header": {"fill_value": fill}, "properties": {"parameter": {"T2M": valores}}}


def test_power_descarta_el_promedio_anual():
    filas = nasa_power.a_filas(
        _respuesta({"202401": 18.1, "202413": 18.5}),
        {"producto": "Papa", "departamento": "Boyaca", "lat": 5.5, "lon": -73.4},
    )
    assert [f["mes"] for f in filas] == [1]


def test_power_convierte_el_centinela_en_nulo():
    filas = nasa_power.a_filas(
        _respuesta({"202401": -999.0}),
        {"producto": "Papa", "departamento": "Boyaca", "lat": 5.5, "lon": -73.4},
    )
    assert filas[0]["valor"] is None


def test_power_usa_el_centinela_que_declara_el_encabezado():
    filas = nasa_power.a_filas(
        _respuesta({"202401": -99.0}, fill=-99.0),
        {"producto": "Papa", "departamento": "Boyaca", "lat": 5.5, "lon": -73.4},
    )
    assert filas[0]["valor"] is None


def test_power_lee_el_anio_limite_del_servicio(monkeypatch):
    """El limite se lee de /configuration, nunca se estima a partir de la fecha."""

    class RespuestaFalsa:
        def raise_for_status(self):
            pass

        def json(self):
            return {"settings": {"end": "2025-12-31T00:00:00"}}

    class SesionFalsa:
        def get(self, url, **kw):
            assert url == nasa_power.CONFIGURACION
            return RespuestaFalsa()

    assert nasa_power.ultimo_anio_disponible(SesionFalsa()) == 2025


# --- Pink Sheet -------------------------------------------------------------

def test_pink_sheet_encuentra_el_excel_mensual():
    html = (FIXTURES / "pink_sheet.html").read_text(encoding="utf-8")
    url = pink_sheet.buscar_excel(html)
    assert url.endswith(".xlsx")
    assert "monthly" in url.lower()


def test_pink_sheet_prefiere_mensual_sobre_anual_sin_importar_el_orden():
    html = '<a href="/a/CMO-Historical-Data-Annual.xlsx">a</a><a href="/b/CMO-Historical-Data-Monthly.xlsx">m</a>'
    assert "Monthly" in pink_sheet.buscar_excel(html)


def test_pink_sheet_sin_enlaces_devuelve_none():
    assert pink_sheet.buscar_excel("<html>nada</html>") is None


# --- Bitacora ---------------------------------------------------------------

def test_bitacora_guarda_y_recupera_la_ultima_exitosa(tmp_path):
    con = conectar(tmp_path / "prueba.duckdb")
    assert ultima_actualizacion_fuente(con, "oni") is None

    registrar(con, ResultadoDescarga("oni", "ok", fecha_actualizacion_fuente=datetime(2026, 1, 1)))
    registrar(con, ResultadoDescarga("oni", "error", fecha_actualizacion_fuente=datetime(2026, 6, 1)))

    # Los fallidos no cuentan: si no, un error marcaria la fuente como al dia.
    assert ultima_actualizacion_fuente(con, "oni") == datetime(2026, 1, 1)
    con.close()
