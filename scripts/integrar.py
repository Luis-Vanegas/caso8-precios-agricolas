"""Fase 3: carga el modelo estrella en DuckDB desde los parquet de interim.

Uso:
    python scripts/integrar.py
    python scripts/integrar.py --verificar   # solo corre los chequeos
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.registro import conectar
from src.common.rutas import BASE_DUCKDB, RAIZ
from src.integration.modelo import compactar, construir
from src.indicators import quiebres, sensibilidad
from src.integration.verificacion import CHEQUEOS, correr_chequeos

log = logging.getLogger("integrar")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verificar", action="store_true", help="no reconstruye, solo verifica")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    con = conectar()

    if not args.verificar:
        print("--- construyendo el modelo ---")
        conteos = construir(con)
        print()
        for tabla, filas in conteos.items():
            print(f"  {tabla:24} {filas:>10,} filas")

        # Indicadores estadisticos: se calculan sobre el modelo ya construido.
        for nombre, calcular in (("indicador_sensibilidad_clima", sensibilidad.construir),
                                 ("indicador_quiebres", quiebres.construir)):
            try:
                tabla = calcular(con)
                con.execute(f"CREATE OR REPLACE TABLE {nombre} AS SELECT * FROM tabla")
                print(f"  {nombre:24} {len(tabla):>10,} filas")
            except Exception as exc:   # falta una tabla opcional: el resto del modelo sigue sirviendo
                log.warning("%s omitido: %s: %s", nombre, type(exc).__name__, exc)

    print("\n--- verificacion de integridad ---")
    fallos = correr_chequeos(con)
    for nombre, resultado in fallos.items():
        estado = "OK  " if resultado.ok else "FALLA"
        print(f"  [{estado}] {nombre}: {resultado.detalle}")

    # El tamaño se mide despues de cerrar: DuckDB hace checkpoint al cerrar y
    # antes de eso el archivo todavia no refleja lo escrito.
    con.close()

    if args.verificar:
        tamano = BASE_DUCKDB.stat().st_size / 1e6
        print(f"\nBase: {BASE_DUCKDB.relative_to(RAIZ)} ({tamano:.1f} MB)")
    else:
        antes, despues = compactar(BASE_DUCKDB)
        print(
            f"\nBase: {BASE_DUCKDB.relative_to(RAIZ)} "
            f"({despues:.1f} MB, compactada desde {antes:.1f} MB)"
        )

    return 0 if all(r.ok for r in fallos.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
