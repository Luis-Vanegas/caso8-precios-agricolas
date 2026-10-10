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


def carpetas_con_datos(base: Path) -> list[Path]:
    """Carpetas de descarga que tienen algun archivo, de la mas vieja a la mas nueva.

    Las vacias se saltan: `carpeta_cruda` crea la carpeta del dia ANTES de
    descargar, asi que una descarga fallida deja una carpeta vacia que taparia
    a la ultima buena (paso con IDEAM el 2026-10-08).
    """
    return sorted(d for d in base.glob("*") if d.is_dir() and any(d.iterdir()))


def archivos_mas_recientes(base: Path, patron: str) -> list[Path]:
    """La version mas reciente de CADA archivo, venga de la carpeta que venga.

    Para fuentes que bajan muchos archivos independientes (IDEAM: uno por
    variable, departamento y ano). Si hoy fallo uno, se usa su ultima copia
    buena en vez de perderlo: el 2026-10-09 una descarga parcial de IDEAM borro
    la lluvia de Antioquia 2025 y Cundinamarca 2024-2025 de la base.
    """
    ultimo: dict[str, Path] = {}
    for carpeta in carpetas_con_datos(base):        # de la mas vieja a la mas nueva
        for archivo in carpeta.glob(patron):
            ultimo[archivo.name] = archivo           # la mas nueva pisa a la vieja
    return sorted(ultimo.values(), key=lambda a: a.name)


def ultima_carpeta_cruda(fuente: str) -> Path:
    """Carpeta de descarga mas reciente (y con datos) de una fuente, sin crear nada.

    La limpieza corre en un dia distinto al de la descarga, asi que no puede
    asumir la carpeta de hoy.
    """
    carpetas = carpetas_con_datos(CRUDO / fuente)
    if not carpetas:
        raise FileNotFoundError(
            f"no hay descargas de '{fuente}'. Correr primero scripts/carga_inicial.py"
        )
    return carpetas[-1]


def carpeta_intermedia(fuente: str) -> Path:
    """data/interim/<fuente>/, creada si no existe."""
    destino = INTERMEDIO / fuente
    destino.mkdir(parents=True, exist_ok=True)
    return destino
