"""ONI (NOAA CPC): fases El Nino / La Nina.

Archivo de texto de ancho fijo con encabezado `SEAS  YR   TOTAL   ANOM`, desde
`DJF 1950`. `ANOM` es la media movil de tres meses de la anomalia de temperatura
del mar en la region Nino 3.4.
"""

from __future__ import annotations

import logging
from datetime import datetime

from src.common.http import sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "oni"
URL = "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt"

UMBRAL = 0.5  # >= +0.5 El Nino, <= -0.5 La Nina, el resto neutral

# Mes central de cada trimestre movil. DJF centra en enero, JJA en julio.
MES_CENTRAL = {
    "DJF": 1, "JFM": 2, "FMA": 3, "MAM": 4, "AMJ": 5, "MJJ": 6,
    "JJA": 7, "JAS": 8, "ASO": 9, "SON": 10, "OND": 11, "NDJ": 12,
}

# Los trimestres mas recientes se revisan hasta dos meses despues de publicados.
TRIMESTRES_PROVISIONALES = 2


def clasificar(anomalia: float) -> str:
    if anomalia >= UMBRAL:
        return "El Nino"
    if anomalia <= -UMBRAL:
        return "La Nina"
    return "Neutral"


def leer(texto: str) -> list[dict]:
    """Parsea el archivo a filas (trimestre, anio, mes_central, anomalia, fase).

    Separada de la descarga para poder probarla con un fixture, sin red.
    """
    filas: list[dict] = []
    for linea in texto.splitlines():
        campos = linea.split()
        if len(campos) != 4 or campos[0] == "SEAS":
            continue
        trimestre, anio, _total, anomalia = campos
        try:
            filas.append(
                {
                    "trimestre": trimestre,
                    "anio": int(anio),
                    "mes_central": MES_CENTRAL[trimestre],
                    "anomalia": float(anomalia),
                    "fase": clasificar(float(anomalia)),
                }
            )
        except (ValueError, KeyError):
            log.warning("linea ONI ilegible: %r", linea)
    # Los ultimos trimestres todavia pueden cambiar: se marcan como provisionales.
    for fila in filas[-TRIMESTRES_PROVISIONALES:]:
        fila["provisional"] = True
    for fila in filas[:-TRIMESTRES_PROVISIONALES]:
        fila["provisional"] = False
    return filas


def estado() -> EstadoFuente:
    try:
        r = sesion().get(URL, timeout=60)
        r.raise_for_status()
        filas = leer(r.text)
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    if not filas:
        return EstadoFuente(FUENTE, disponible=False, detalle="archivo sin filas legibles")
    ultima = filas[-1]
    return EstadoFuente(
        fuente=FUENTE,
        disponible=True,
        ultimo_periodo=f"{ultima['trimestre']} {ultima['anio']}",
        detalle=f"anomalia {ultima['anomalia']:+.2f} -> {ultima['fase']} (provisional)",
    )


def descargar(desde: datetime | None = None, forzar: bool = False) -> ResultadoDescarga:
    destino = carpeta_cruda(FUENTE) / "oni.ascii.txt"
    if destino.exists() and not forzar:
        filas = leer(destino.read_text(encoding="utf-8"))
        ultima = filas[-1] if filas else None
        return ResultadoDescarga(
            FUENTE,
            "cache",
            archivos=[str(destino)],
            filas=len(filas),
            ultimo_periodo=f"{ultima['trimestre']} {ultima['anio']}" if ultima else None,
            mensaje="ya descargado hoy",
        )
    try:
        r = sesion().get(URL, timeout=60)
        r.raise_for_status()
        destino.write_bytes(r.content)
        filas = leer(r.text)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    ultima = filas[-1] if filas else None
    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok",
        archivos=[str(destino)],
        filas=len(filas),
        ultimo_periodo=f"{ultima['trimestre']} {ultima['anio']}" if ultima else None,
        mensaje=f"fase actual: {ultima['fase']}" if ultima else "",
    )
