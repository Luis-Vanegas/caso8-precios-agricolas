"""Pink Sheet (Banco Mundial): precios mensuales de commodities. Fuente opcional.

La URL del Excel cambia cada mes, asi que se descubre leyendo el HTML de la
pagina. Nunca se escribe a mano.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime
from urllib.parse import urljoin

from src.common.http import descargar_a_archivo, sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "pink_sheet"
PAGINA = "https://www.worldbank.org/en/research/commodity-markets"

# Enlaces a hojas de calculo. El nombre del archivo mensual arranca con "CMO"
# (Commodity Markets Outlook), pero se acepta cualquier xlsx y se prioriza CMO.
_ENLACE = re.compile(r'href=["\']([^"\']+\.xlsx?)["\']', re.IGNORECASE)


def buscar_excel(html: str, base: str = PAGINA) -> str | None:
    """Devuelve la URL absoluta del Excel mensual, o None si no aparece.

    Separada de la descarga para poder probarla con un fixture, sin red.
    """
    enlaces = [urljoin(base, u) for u in _ENLACE.findall(html)]
    if not enlaces:
        return None
    # La pagina publica tambien la serie anual; queremos la mensual. No se
    # confia en el orden en que aparezcan los enlaces.
    mensual = [u for u in enlaces if "monthly" in u.lower()]
    con_cmo = [u for u in enlaces if "cmo" in u.lower()]
    return (mensual or con_cmo or enlaces)[0]


def estado() -> EstadoFuente:
    try:
        r = sesion().get(PAGINA, timeout=120)
        r.raise_for_status()
        url = buscar_excel(r.text)
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    if not url:
        return EstadoFuente(
            FUENTE, disponible=False, detalle="la pagina responde pero no expone ningun xlsx"
        )
    return EstadoFuente(fuente=FUENTE, disponible=True, detalle=url)


def descargar(desde: datetime | None = None, forzar: bool = False) -> ResultadoDescarga:
    try:
        r = sesion().get(PAGINA, timeout=120)
        r.raise_for_status()
        url = buscar_excel(r.text)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")
    if not url:
        return ResultadoDescarga(
            FUENTE, "error", mensaje="no se encontro el enlace al Excel en la pagina"
        )

    destino = carpeta_cruda(FUENTE) / url.rsplit("/", 1)[-1]
    ya_estaba = destino.exists()
    try:
        descargar_a_archivo(url, destino, forzar=forzar)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    return ResultadoDescarga(
        fuente=FUENTE,
        estado="cache" if ya_estaba and not forzar else "ok",
        archivos=[str(destino)],
        mensaje=url,
    )
