"""FAOSTAT: descargas masivas desde el catalogo XML.

Es la via principal de carga historica y no necesita credenciales. La API REST
solo se usa para actualizaciones incrementales (ver `faostat_api.py`).

Campos reales del catalogo, verificados en Fase 0: DatasetCode, DatasetName,
DateUpdate, FileSize, FileRows, FileLocation.
"""

from __future__ import annotations

import logging
import defusedxml.ElementTree as ET  # bloquea expansion de entidades (dato remoto)
from datetime import datetime
from pathlib import Path

from src.common.http import descargar_a_archivo, sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "faostat_bulk"
CATALOGO = "https://bulks-faostat.fao.org/production/datasets_E.xml"

# Los seis dominios del caso. El resto del catalogo (69 datasets) no se toca.
DOMINIOS = ("PP", "QCL", "TCL", "FBS", "QV", "PE")


def leer_catalogo(xml: bytes) -> dict[str, dict]:
    """Extrae del catalogo solo los dominios que interesan.

    Se separa de la descarga para poder probarla con un XML de fixture,
    sin red.
    """
    raiz = ET.fromstring(xml)
    encontrados: dict[str, dict] = {}
    for ds in raiz.findall(".//Dataset"):
        codigo = (ds.findtext("DatasetCode") or "").strip()
        if codigo not in DOMINIOS:
            continue
        # El catalogo trae varias entradas por dominio (normalizada y ancha).
        # Nos quedamos con la normalizada, que es la que manda el CLAUDE.md.
        ubicacion = (ds.findtext("FileLocation") or "").strip()
        if "(Normalized)" not in ubicacion:
            continue
        encontrados[codigo] = {
            "codigo": codigo,
            "nombre": (ds.findtext("DatasetName") or "").strip(),
            "url": ubicacion,
            "actualizado": _fecha(ds.findtext("DateUpdate")),
            "tamano": (ds.findtext("FileSize") or "").strip(),
            "filas": _entero(ds.findtext("FileRows")),
        }
    return encontrados


def _fecha(texto: str | None) -> datetime | None:
    """DateUpdate llega como '2026-04-30T00:00:00'."""
    if not texto:
        return None
    try:
        return datetime.fromisoformat(texto.strip())
    except ValueError:
        log.warning("DateUpdate con formato inesperado: %r", texto)
        return None


def _entero(texto: str | None) -> int | None:
    try:
        return int((texto or "").strip())
    except ValueError:
        return None


def estado() -> EstadoFuente:
    """Lee el catalogo y reporta la fecha de actualizacion mas reciente."""
    ses = sesion()
    try:
        r = ses.get(CATALOGO, timeout=120)
        r.raise_for_status()
        datasets = leer_catalogo(r.content)
    except Exception as exc:  # red o XML mal formado
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")

    faltantes = set(DOMINIOS) - set(datasets)
    if faltantes:
        log.warning("dominios ausentes del catalogo: %s", sorted(faltantes))

    fechas = [d["actualizado"] for d in datasets.values() if d["actualizado"]]
    mas_reciente = max(fechas) if fechas else None
    detalle = ", ".join(
        f"{c}={d['actualizado'].date() if d['actualizado'] else '?'}"
        for c, d in sorted(datasets.items())
    )
    return EstadoFuente(
        fuente=FUENTE,
        disponible=True,
        ultimo_periodo=mas_reciente.date().isoformat() if mas_reciente else None,
        fecha_actualizacion_fuente=mas_reciente,
        detalle=detalle,
    )


def descargar(desde: datetime | None = None, forzar: bool = False) -> ResultadoDescarga:
    """Baja los zip de los dominios actualizados despues de `desde`.

    Con `desde=None` baja los seis, que es el caso de la carga inicial.
    """
    ses = sesion()
    try:
        r = ses.get(CATALOGO, timeout=120)
        r.raise_for_status()
        datasets = leer_catalogo(r.content)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    destino = carpeta_cruda(FUENTE)
    # El catalogo se guarda tambien: es la evidencia de que fechas tenia la
    # fuente el dia de la descarga.
    (destino / "datasets_E.xml").write_bytes(r.content)

    archivos: list[str] = []
    filas = 0
    errores: list[str] = []
    for codigo in DOMINIOS:
        info = datasets.get(codigo)
        if not info:
            errores.append(f"{codigo}: ausente del catalogo")
            continue
        if desde and info["actualizado"] and info["actualizado"] <= desde and not forzar:
            log.info("%s sin cambios desde %s", codigo, desde.date())
            continue
        archivo = destino / Path(info["url"]).name
        try:
            descargar_a_archivo(info["url"], archivo, ses=ses, forzar=forzar)
        except Exception as exc:
            errores.append(f"{codigo}: {type(exc).__name__}")
            continue
        archivos.append(str(archivo))
        filas += info["filas"] or 0

    fechas = [d["actualizado"] for d in datasets.values() if d["actualizado"]]
    mas_reciente = max(fechas) if fechas else None

    if errores and not archivos:
        return ResultadoDescarga(FUENTE, "error", mensaje="; ".join(errores))
    if not archivos:
        return ResultadoDescarga(
            FUENTE,
            "cache",
            ultimo_periodo=mas_reciente.date().isoformat() if mas_reciente else None,
            fecha_actualizacion_fuente=mas_reciente,
            mensaje="sin dominios nuevos",
        )
    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok",
        archivos=archivos,
        filas=filas or None,
        ultimo_periodo=mas_reciente.date().isoformat() if mas_reciente else None,
        fecha_actualizacion_fuente=mas_reciente,
        mensaje="; ".join(errores),
    )
