"""Tests del orquestador diario. No corre los scripts reales: usa un ejecutor falso."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts import diario


def _ejecutor(codigos: dict[str, int], corridos: list[str]):
    def ejecutar(script: str) -> int:
        corridos.append(script)
        return codigos.get(script, 0)
    return ejecutar


def test_todo_bien_corre_los_tres_pasos_en_orden():
    corridos: list[str] = []
    assert diario.correr(_ejecutor({}, corridos)) == 0
    assert corridos == ["actualizar.py", "preparar.py", "integrar.py"]


def test_una_fuente_caida_no_frena_la_cadena_pero_se_avisa():
    # actualizar.py devuelve 1 si ALGUNA fuente fallo: se sigue con los datos que haya
    corridos: list[str] = []
    assert diario.correr(_ejecutor({"actualizar.py": 1}, corridos)) == 1
    assert corridos == ["actualizar.py", "preparar.py", "integrar.py"]


def test_si_falla_la_limpieza_no_se_integra():
    # Integrar con una limpieza rota dejaria la base a medio armar
    corridos: list[str] = []
    assert diario.correr(_ejecutor({"preparar.py": 1}, corridos)) == 1
    assert corridos == ["actualizar.py", "preparar.py"]
