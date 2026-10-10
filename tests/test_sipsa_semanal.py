"""Tests de los precios semanales de SIPSA. Ninguno toca la red.

La fixture es un recorte real de `promediosSipsaSemanaMadr` descargado el
2026-10-09. Trae a proposito un articulo de cada unidad: huevo (por unidad),
papa (por kg) y aceite (por litro).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import sipsa, sipsa_semanal

FIXTURE = Path(__file__).parent / "fixtures" / "sipsa_semanal.xml"


def test_parsea_los_campos_reales():
    registros = sipsa_semanal.leer_registros(FIXTURE)
    assert len(registros) == 3
    assert set(registros[0]) == {
        "artiId", "artiNombre", "fechaIni", "fuenId", "fuenNombre",
        "futiId", "maximoKg", "minimoKg", "promedioKg",
    }


def test_ultima_semana_es_la_mayor():
    registros = sipsa_semanal.leer_registros(FIXTURE)
    assert sipsa_semanal.ultima_semana(registros) == "2026-10-03"


def test_descargar_usa_el_metodo_semanal(tmp_path, monkeypatch):
    llamadas = []

    def invocar_falso(metodo, destino, ses=None):
        llamadas.append(metodo)
        shutil.copy(FIXTURE, destino)
        return destino

    monkeypatch.setattr(sipsa, "invocar", invocar_falso)
    monkeypatch.setattr(sipsa_semanal, "carpeta_cruda", lambda fuente: tmp_path)

    resultado = sipsa_semanal.descargar()

    assert llamadas == ["promediosSipsaSemanaMadr"]
    assert resultado.estado == "ok"
    assert resultado.filas == 3
    assert resultado.ultimo_periodo == "2026-10-03"
    assert resultado.fuente == "sipsa_semanal"
