"""Rutas del proyecto en un solo lugar, para que ningun modulo arme paths a mano."""

from __future__ import annotations

from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]

DATOS = RAIZ / "data"
CRUDO = DATOS / "raw"
INTERMEDIO = DATOS / "interim"
PROCESADO = DATOS / "processed"
OPENREFINE = DATOS / "openrefine"
CONFIG = RAIZ / "config"

BASE_DUCKDB = PROCESADO / "caso8.duckdb"


def carpeta_cruda(fuente: str, dia: date | None = None) -> Path:
    """data/raw/<fuente>/<AAAA-MM-DD>/, creada si no existe.

    Los datos crudos son inmutables: cada descarga vive en la carpeta del dia
    en que se hizo y nunca se sobreescribe una anterior.
    """
    dia = dia or date.today()
    destino = CRUDO / fuente / dia.isoformat()
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def carpeta_intermedia(fuente: str) -> Path:
    """data/interim/<fuente>/, creada si no existe."""
    destino = INTERMEDIO / fuente
    destino.mkdir(parents=True, exist_ok=True)
    return destino
