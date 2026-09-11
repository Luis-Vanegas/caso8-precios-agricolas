"""Tipos compartidos por todos los modulos de adquisicion.

El contrato es el mismo para las seis fuentes: cada modulo expone
`estado()` y `descargar()`. Eso permite que `actualizar.py` las recorra en
un bucle en vez de encadenar condicionales por fuente.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class EstadoFuente:
    """Respuesta de `estado()`: que tan fresca esta la fuente, sin descargar nada."""

    fuente: str
    disponible: bool
    # Ultimo periodo con dato segun la fuente, en el formato propio de cada una
    # (por ejemplo "2026-09-10" para SIPSA o "2026-07-24" para un dominio de FAOSTAT).
    ultimo_periodo: str | None = None
    # Fecha de actualizacion que reporta la fuente, cuando la publica.
    fecha_actualizacion_fuente: datetime | None = None
    detalle: str = ""


@dataclass
class ResultadoDescarga:
    """Respuesta de `descargar()`: que se trajo y como termino."""

    fuente: str
    # "ok" descargo algo nuevo | "cache" ya estaba al dia | "error" fallo
    estado: str
    archivos: list[str] = field(default_factory=list)
    filas: int | None = None
    ultimo_periodo: str | None = None
    fecha_actualizacion_fuente: datetime | None = None
    mensaje: str = ""
