"""SIPSA (DANE): precios mayoristas semanales por articulo y mercado.

Es la fuente de la canasta familiar: 351 articulos (arroz, huevo, pollo, carnes,
aceite, panela, queso, 17 papas...) en 80 mercados. Mismo servicio SOAP que
`sipsa.py`, asi que reusa su `invocar` y su `leer_registros`.

Verificado el 2026-10-09 (ver `docs/verificacion_api.md`):
- Campos: artiId, artiNombre, fechaIni, fuenId, fuenNombre, futiId,
  maximoKg, minimoKg, promedioKg.
- 230312 filas (~67 MB). Dos llamadas el mismo dia devolvieron lo mismo.
- OJO 1: el servicio solo trae las ultimas ~51 semanas. La historia se arma
  guardando cada descarga en su carpeta del dia (datos crudos inmutables) y
  uniendolas en la limpieza.
- OJO 2: el campo se llama `promedioKg`, pero el huevo y el bocadillo van por
  unidad y el aceite, el jugo y el vinagre por litro (Metodologia SIPSA-P, p. 16).
  La unidad se asigna en la limpieza, no aca.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from src.acquisition import sipsa
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

FUENTE = "sipsa_semanal"
METODO = "promediosSipsaSemanaMadr"


def leer_registros(ruta: Path) -> list[dict]:
    """Mismo formato SOAP que los precios diarios: se reusa el parser de `sipsa`."""
    return sipsa.leer_registros(ruta)


def ultima_semana(registros: list[dict]) -> str | None:
    """Inicio de la semana mas reciente con dato, en formato AAAA-MM-DD."""
    fechas = [r["fechaIni"][:10] for r in registros if r.get("fechaIni")]
    return max(fechas) if fechas else None


def estado() -> EstadoFuente:
    """El servicio es el mismo de los precios diarios: si su WSDL responde, este tambien."""
    e = sipsa.estado()
    return EstadoFuente(FUENTE, disponible=e.disponible, detalle=e.detalle)


def descargar(forzar: bool = False) -> ResultadoDescarga:
    """Invoca el metodo y guarda la foto de hoy. Las fotos viejas no se tocan."""
    destino = carpeta_cruda(FUENTE) / f"{METODO}.xml"
    if destino.exists() and not forzar:
        registros = leer_registros(destino)
        return ResultadoDescarga(FUENTE, "cache", archivos=[str(destino)], filas=len(registros),
                                 ultimo_periodo=ultima_semana(registros), mensaje="ya descargado hoy")
    try:
        sipsa.invocar(METODO, destino)
        registros = leer_registros(destino)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok",
        archivos=[str(destino)],
        filas=len(registros),
        ultimo_periodo=ultima_semana(registros),
        fecha_actualizacion_fuente=datetime.now(),
        mensaje=METODO,
    )
