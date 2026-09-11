"""NASA POWER: clima mensual por punto, sin llave de acceso.

Parametros verificados en Fase 0 contra la OpenAPI y una consulta real:
`start`, `end`, `latitude`, `longitude`, `community`, `parameters` son
obligatorios. La respuesta llega en `properties.parameter.<PARAM>` con claves
`AAAAMM`.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime

from src.common.http import sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import CONFIG, carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "nasa_power"
ENDPOINT = "https://power.larc.nasa.gov/api/temporal/monthly/point"
CONFIGURACION = "https://power.larc.nasa.gov/api/temporal/monthly/configuration"

# PRECTOTCORR: precipitacion corregida. T2M: temperatura a 2 metros.
PARAMETROS = "PRECTOTCORR,T2M"
COMUNIDAD = "ag"  # agroclimatologia

# Valor centinela de POWER para dato faltante. Si no se filtra, un -999 entra
# como si fuera una temperatura y arruina cualquier promedio.
SIN_DATO = -999.0

ANIO_INICIO = 1991  # arranca junto con la serie anual de precios productor de FAO


def zonas() -> list[dict]:
    """Lee las zonas productoras del archivo de configuracion."""
    datos = json.loads((CONFIG / "zonas_productoras.json").read_text(encoding="utf-8"))
    return datos["zonas"]


def ultimo_anio_disponible(ses=None) -> int:
    """Ultimo anio que el endpoint mensual realmente sirve, leido del servicio.

    El endpoint mensual no trabaja por mes cerrado sino por anio completo, y va
    con mas de un anio de rezago: en septiembre de 2026 solo llegaba hasta
    2025-12-31. Pedir el anio en curso devuelve 422. El propio servicio publica
    el limite en `/configuration`, asi que se lee de ahi en vez de estimarlo.
    """
    ses = ses or sesion()
    r = ses.get(CONFIGURACION, timeout=60)
    r.raise_for_status()
    return int(r.json()["settings"]["end"][:4])


def a_filas(respuesta: dict, zona: dict) -> list[dict]:
    """Aplana la respuesta de POWER a filas (zona, anio, mes, parametro, valor).

    POWER agrega una clave `<anio>13` con el promedio anual del parametro. Se
    descarta: no es un mes.
    """
    parametros = respuesta["properties"]["parameter"]
    # POWER declara su centinela en el encabezado; se usa ese y no el valor fijo.
    sin_dato = respuesta.get("header", {}).get("fill_value", SIN_DATO)
    filas: list[dict] = []
    for nombre, serie in parametros.items():
        for clave, valor in serie.items():
            anio, mes = int(clave[:4]), int(clave[4:])
            if mes == 13:
                continue
            filas.append(
                {
                    "producto": zona["producto"],
                    "departamento": zona["departamento"],
                    "lat": zona["lat"],
                    "lon": zona["lon"],
                    "anio": anio,
                    "mes": mes,
                    "parametro": nombre,
                    "valor": None if valor == sin_dato else valor,
                }
            )
    return filas


def estado() -> EstadoFuente:
    """El servicio no publica fecha de actualizacion: se reporta el anio servido."""
    ses = sesion()
    try:
        anio = ultimo_anio_disponible(ses)
        r = ses.get(
            ENDPOINT,
            params={
                "start": anio,
                "end": anio,
                "latitude": 4.65,
                "longitude": -74.08,
                "community": COMUNIDAD,
                "parameters": "T2M",
                "format": "JSON",
            },
            timeout=120,
        )
        r.raise_for_status()
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    return EstadoFuente(
        fuente=FUENTE,
        disponible=True,
        ultimo_periodo=str(anio),
        detalle=f"anio mas reciente servido por el endpoint mensual: {anio}",
    )


def descargar(desde: datetime | None = None, forzar: bool = False) -> ResultadoDescarga:
    """Una consulta por zona productora. `desde` se ignora: POWER revisa el historico."""
    destino = carpeta_cruda(FUENTE)
    ses = sesion()
    try:
        anio_fin = ultimo_anio_disponible(ses)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    archivos: list[str] = []
    filas = 0
    errores: list[str] = []
    for zona in zonas():
        nombre = f"{zona['producto']}_{zona['departamento']}.json".replace(" ", "_")
        archivo = destino / nombre
        if archivo.exists() and not forzar:
            archivos.append(str(archivo))
            continue
        try:
            r = ses.get(
                ENDPOINT,
                params={
                    "start": ANIO_INICIO,
                    "end": anio_fin,
                    "latitude": zona["lat"],
                    "longitude": zona["lon"],
                    "community": COMUNIDAD,
                    "parameters": PARAMETROS,
                    "format": "JSON",
                },
                timeout=180,
            )
            r.raise_for_status()
            archivo.write_bytes(r.content)
            filas += len(a_filas(r.json(), zona))
        except Exception as exc:
            errores.append(f"{nombre}: {type(exc).__name__}")
            continue
        archivos.append(str(archivo))

    if errores and not archivos:
        return ResultadoDescarga(FUENTE, "error", mensaje="; ".join(errores))
    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok" if filas else "cache",
        archivos=archivos,
        filas=filas or None,
        ultimo_periodo=str(anio_fin),
        mensaje="; ".join(errores),
    )
