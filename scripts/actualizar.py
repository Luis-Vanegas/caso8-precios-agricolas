"""Actualiza las fuentes que tengan datos nuevos y deja constancia en DuckDB.

Es idempotente: correrlo dos veces seguidas no vuelve a descargar nada.

Uso:
    python scripts/actualizar.py                  # todas las fuentes
    python scripts/actualizar.py --solo sipsa     # una sola
    python scripts/actualizar.py --dry-run        # informa, no descarga
    python scripts/actualizar.py --forzar         # ignora lo ya descargado
"""

from __future__ import annotations

import argparse
import os
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import (
    faostat_api, faostat_bulk, ideam, nasa_power, nasa_power_diario, oni, pink_sheet, sipsa,
    sipsa_abastecimiento, sipsa_semanal, open_meteo,
)
from src.common.modelos import ResultadoDescarga
from src.common.registro import conectar, registrar, resumen_frescura, ultima_actualizacion_fuente

# Registro de fuentes. Agregar una fuente es agregar una linea aca, no tocar
# el flujo. Todas exponen el mismo par `estado()` / `descargar()`.
FUENTES = {
    "faostat_bulk": faostat_bulk,
    "sipsa": sipsa,
    "sipsa_abastecimiento": sipsa_abastecimiento,
    "sipsa_semanal": sipsa_semanal,
    "open_meteo": open_meteo,
    "nasa_power": nasa_power,
    "nasa_power_diario": nasa_power_diario,
    "oni": oni,
    "pink_sheet": pink_sheet,
    "ideam": ideam,
}
# La API de FAOSTAT exige token. Sin el, fallaria TODOS los dias y la corrida
# diaria quedaria siempre "con errores": el equipo dejaria de mirar el aviso y
# no veria una falla real. La historia de FAOSTAT ya sale de `faostat_bulk`.
if os.environ.get("FAOSTAT_API_KEY"):
    FUENTES["faostat_api"] = faostat_api

log = logging.getLogger("actualizar")


def actualizar_una(nombre: str, con, forzar: bool, dry_run: bool) -> ResultadoDescarga:
    """Consulta el estado de una fuente y, si corresponde, la descarga."""
    modulo = FUENTES[nombre]
    estado = modulo.estado()
    log.info("%-14s disponible=%s ultimo=%s %s",
             nombre, estado.disponible, estado.ultimo_periodo, estado.detalle[:80])

    if not estado.disponible:
        return ResultadoDescarga(nombre, "error", mensaje=estado.detalle)

    previa = ultima_actualizacion_fuente(con, nombre)
    sin_cambios = (
        not forzar
        and previa is not None
        and estado.fecha_actualizacion_fuente is not None
        and estado.fecha_actualizacion_fuente <= previa
    )
    if sin_cambios:
        return ResultadoDescarga(
            nombre,
            "cache",
            ultimo_periodo=estado.ultimo_periodo,
            fecha_actualizacion_fuente=estado.fecha_actualizacion_fuente,
            mensaje=f"sin cambios desde {previa:%Y-%m-%d}",
        )

    if dry_run:
        return ResultadoDescarga(
            nombre,
            "cache",
            ultimo_periodo=estado.ultimo_periodo,
            fecha_actualizacion_fuente=estado.fecha_actualizacion_fuente,
            mensaje="dry-run: se habria descargado",
        )

    return modulo.descargar(forzar=forzar)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo", choices=sorted(FUENTES), help="actualizar una sola fuente")
    parser.add_argument("--dry-run", action="store_true", help="informa sin descargar")
    parser.add_argument("--forzar", action="store_true", help="descarga aunque no haya cambios")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    seleccion = [args.solo] if args.solo else list(FUENTES)

    con = conectar()
    resultados: list[ResultadoDescarga] = []
    for nombre in seleccion:
        try:
            resultado = actualizar_una(nombre, con, args.forzar, args.dry_run)
        except Exception as exc:  # una fuente caida no tumba a las demas
            log.exception("fallo inesperado en %s", nombre)
            resultado = ResultadoDescarga(nombre, "error", mensaje=f"{type(exc).__name__}: {exc}")
        # El dry-run no ensucia la bitacora.
        if not args.dry_run:
            registrar(con, resultado)
        resultados.append(resultado)

    print("\n--- resumen ---")
    for r in resultados:
        filas = f"{r.filas:,}" if r.filas else "-"
        print(f"{r.estado.upper():6} {r.fuente:14} ultimo={r.ultimo_periodo or '-':12} "
              f"filas={filas:>12}  {r.mensaje[:70]}")

    if not args.dry_run:
        print("\n--- frescura registrada ---")
        print(resumen_frescura(con).to_string(index=False))
    con.close()

    # Codigo de salida distinto de cero si alguna fuente fallo, para que se note
    # en una corrida automatica.
    return 1 if any(r.estado == "error" for r in resultados) else 0


if __name__ == "__main__":
    sys.exit(main())
