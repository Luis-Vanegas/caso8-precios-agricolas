"""SIPSA (DANE): abastecimiento mensual de alimentos en las centrales mayoristas.

Dice cuantas toneladas de cada alimento entraron a cada central cada mes. Es el
eslabon del medio de la cadena del proyecto: clima -> oferta -> precio.

Usa el mismo servicio SOAP que `sipsa.py` (mismo endpoint HTTPS y SOAP 1.2), asi
que reusa su `invocar` y su `leer_registros`; aca solo cambia el metodo.

Verificado el 2026-10-09 (ver `docs/verificacion_api.md`):
- Campos: artiId, artiNombre, cantidadTon, fechaMesIni, fuenId, fuenNombre, futiId.
- 164274 filas, 194 articulos, 34 centrales, de 2020-02 a 2026-07 (~40 MB).
- Dos llamadas el mismo dia devolvieron las mismas filas y los mismos bytes:
  pese al sufijo `Madr`, no filtra por la bandera `enviado`.
- `artiId` es el mismo codigo que usan los precios semanales: sirve de llave.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.acquisition import sipsa
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

FUENTE = "sipsa_abastecimiento"
METODO = "promedioAbasSipsaMesMadr"


def leer_registros(ruta: Path) -> list[dict]:
    """Mismo formato SOAP que los precios: se reusa el parser de `sipsa`."""
    return sipsa.leer_registros(ruta)


def ultimo_mes(registros: list[dict]) -> str | None:
    """Mes mas reciente con dato, en formato AAAA-MM."""
    meses = [r["fechaMesIni"][:7] for r in registros if r.get("fechaMesIni")]
    return max(meses) if meses else None


def estado() -> EstadoFuente:
    """El servicio es el mismo de los precios: si su WSDL responde, este tambien."""
    e = sipsa.estado()
    return EstadoFuente(FUENTE, disponible=e.disponible, detalle=e.detalle)


def descargar(forzar: bool = False) -> ResultadoDescarga:
    """Invoca el metodo, guarda el crudo del dia y cuenta las filas."""
    destino = carpeta_cruda(FUENTE) / f"{METODO}.xml"
    if destino.exists() and not forzar:
        registros = leer_registros(destino)
        return ResultadoDescarga(FUENTE, "cache", archivos=[str(destino)], filas=len(registros),
                                 ultimo_periodo=ultimo_mes(registros), mensaje="ya descargado hoy")
    try:
        sipsa.invocar(METODO, destino)
        registros = leer_registros(destino)
    except Exception as exc:
        # Si fallo el parseo, el crudo igual quedo en disco (lo escribe `invocar`).
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok",
        archivos=[str(destino)],
        filas=len(registros),
        ultimo_periodo=ultimo_mes(registros),
        fecha_actualizacion_fuente=datetime.now(),
        mensaje=METODO,
    )
