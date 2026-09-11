"""FAOSTAT: API REST para actualizaciones incrementales.

# TODO VERIFICAR - Este modulo esta escrito contra lo unico que se pudo
# comprobar en Fase 0 sin credenciales:
#
#   - La URL base valida es faostatservices.fao.org. La otra candidata,
#     fenixservices.fao.org, devuelve 521 (servidor origen caido).
#   - Sin token responde 401 con el cuerpo "Missing Authorization Header",
#     o sea que la autenticacion va por cabecera, no por parametro de consulta.
#
# Lo que NO se pudo verificar y hay que confirmar con un token en la mano:
#   - El esquema exacto de la cabecera (se asume "Bearer <token>").
#   - Las rutas reales y sus parametros.
#   - El limite de 2 peticiones por segundo que reporta el cliente comunitario.
#
# Mientras tanto la carga historica sale de `faostat_bulk`, que no necesita
# credenciales. Este modulo no bloquea el pipeline.

Ojo con los codigos de elemento: el codigo para filtrar no es el mismo que
aparece en los datos. En QCL se filtra por 2510 y en la respuesta viene 5510
("Production quantity"). Area, item y anio si coinciden.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime

from src.common.http import LimitadorTasa, sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "faostat_api"
BASE = "https://faostatservices.fao.org/api/v1"

AREA_COLOMBIA = 44  # codigo de area FAO
LIMITE = LimitadorTasa(2)  # 2 peticiones por segundo, segun el cliente comunitario


class FaltaToken(RuntimeError):
    """No hay FAOSTAT_API_KEY en el entorno."""


def _cabeceras() -> dict[str, str]:
    token = os.environ.get("FAOSTAT_API_KEY")
    if not token:
        raise FaltaToken(
            "falta FAOSTAT_API_KEY en el entorno. Obtener token en el Developer "
            "Portal de FAO y cargarlo en .env (ver docs/verificacion_api.md)"
        )
    return {"Authorization": f"Bearer {token}"}  # TODO VERIFICAR el esquema


def consultar(ruta: str, parametros: dict | None = None) -> dict:
    """GET a la API respetando el limite de tasa. Lanza si el token falta o falla."""
    LIMITE.esperar()
    r = sesion().get(
        f"{BASE}{ruta}", params=parametros, headers=_cabeceras(), timeout=120
    )
    r.raise_for_status()
    return r.json()


def estado() -> EstadoFuente:
    """Comprueba si hay token y si la API lo acepta."""
    try:
        _cabeceras()
    except FaltaToken as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=str(exc))
    try:
        consultar("/en/domains")
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    return EstadoFuente(fuente=FUENTE, disponible=True, detalle="token aceptado")


def descargar(desde: datetime | None = None, forzar: bool = False) -> ResultadoDescarga:
    """Sin token no falla el pipeline: reporta el estado y sigue de largo."""
    try:
        _cabeceras()
    except FaltaToken as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=str(exc))

    # TODO VERIFICAR las rutas reales antes de implementar la descarga por dominio.
    try:
        dominios = consultar("/en/domains")
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    destino = carpeta_cruda(FUENTE) / "domains.json"
    destino.write_text(str(dominios), encoding="utf-8")
    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok",
        archivos=[str(destino)],
        mensaje="solo listado de dominios; rutas de datos pendientes de verificar",
    )
