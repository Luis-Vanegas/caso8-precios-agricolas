"""Tests del abastecimiento de SIPSA. Ninguno toca la red.

La fixture es un recorte real de `promedioAbasSipsaMesMadr` descargado el
2026-10-09 (3 de las 164274 filas).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import sipsa, sipsa_abastecimiento

FIXTURE = Path(__file__).parent / "fixtures" / "sipsa_abastecimiento.xml"


def test_parsea_los_campos_reales():
    registros = sipsa_abastecimiento.leer_registros(FIXTURE)
    assert len(registros) == 3
    assert set(registros[0]) == {
        "artiId", "artiNombre", "cantidadTon", "fechaMesIni",
        "fuenId", "fuenNombre", "futiId",
    }
    # Las tildes del nombre de la central llegan bien
    assert registros[1]["fuenNombre"] == "Bogotá, D.C., Corabastos"


def test_ultimo_mes_es_el_mayor():
    registros = sipsa_abastecimiento.leer_registros(FIXTURE)
    assert sipsa_abastecimiento.ultimo_mes(registros) == "2026-07"


def test_descargar_usa_el_metodo_de_abastecimiento(tmp_path, monkeypatch):
    llamadas = []

    def invocar_falso(metodo, destino, ses=None):
        # En vez de ir a la red, copia la fixture donde iria la respuesta
        llamadas.append(metodo)
        shutil.copy(FIXTURE, destino)
        return destino

    monkeypatch.setattr(sipsa, "invocar", invocar_falso)
    monkeypatch.setattr(sipsa_abastecimiento, "carpeta_cruda", lambda fuente: tmp_path)

    resultado = sipsa_abastecimiento.descargar()

    assert llamadas == ["promedioAbasSipsaMesMadr"]
    assert resultado.estado == "ok"
    assert resultado.filas == 3
    assert resultado.ultimo_periodo == "2026-07"
    assert resultado.fuente == "sipsa_abastecimiento"
