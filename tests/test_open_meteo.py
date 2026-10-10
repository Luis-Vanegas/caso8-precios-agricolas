"""Tests de Open-Meteo. Ninguno toca la red.

Las fixtures son recortes reales del 2026-10-09 para Tunja (Boyaca): 3 dias
observados, 3 de pronostico y 4 del estacional (con solo 2 de sus 50 miembros
y uno de los dias vacios del final).
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import open_meteo

FIXTURES = Path(__file__).parent / "fixtures"
HOY = date(2026, 10, 9)


def _fixture(tipo: str) -> dict:
    return json.loads((FIXTURES / f"open_meteo_{tipo}.json").read_text(encoding="utf-8"))


def test_un_punto_por_departamento_productor():
    deptos = open_meteo.departamentos()
    nombres = [d["departamento"] for d in deptos]
    assert len(nombres) == len(set(nombres)) == 8   # sin repetir Boyaca por papa y cebolla
    assert all({"lat", "lon"} <= set(d) for d in deptos)


def test_observado_va_desde_2020_hasta_ayer():
    url, params = open_meteo.consulta("observado", {"lat": 5.54, "lon": -73.36}, HOY)
    assert "archive-api" in url
    assert params["start_date"] == "2020-01-01"
    assert params["end_date"] == "2026-10-08"


def test_pronostico_16_dias_y_estacional_6_meses():
    _, p = open_meteo.consulta("pronostico", {"lat": 5.54, "lon": -73.36}, HOY)
    _, e = open_meteo.consulta("estacional", {"lat": 5.54, "lon": -73.36}, HOY)
    assert p["forecast_days"] == 16
    assert e["forecast_days"] == 183


def test_cuenta_solo_los_dias_con_lluvia_reportada():
    # El ultimo dia del estacional llega vacio (None): no cuenta
    assert open_meteo.dias_con_dato(_fixture("estacional")) == 3
    assert open_meteo.dias_con_dato(_fixture("observado")) == 3


class _Respuesta:
    def __init__(self, datos):
        self._datos = datos
        self.content = json.dumps(datos).encode("utf-8")

    def raise_for_status(self):
        pass

    def json(self):
        return self._datos


class _SesionFalsa:
    """Devuelve la fixture que corresponde a cada endpoint, sin ir a la red."""

    def get(self, url, params=None, timeout=None):
        tipo = {"archive-api": "observado", "seasonal-api": "estacional"}.get(
            url.split("//")[1].split(".")[0], "pronostico")
        return _Respuesta(_fixture(tipo))


def test_descargar_guarda_tres_archivos_por_departamento(tmp_path, monkeypatch):
    monkeypatch.setattr(open_meteo, "carpeta_cruda", lambda fuente: tmp_path)
    monkeypatch.setattr(open_meteo, "sesion", lambda: _SesionFalsa())

    resultado = open_meteo.descargar()

    assert resultado.estado == "ok"
    assert len(resultado.archivos) == 8 * 3
    assert (tmp_path / "estacional_Boyaca.json").exists()
    assert resultado.ultimo_periodo == "2026-10-08"   # ultimo dia observado
