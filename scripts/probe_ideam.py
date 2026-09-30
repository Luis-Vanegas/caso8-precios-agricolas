"""Verifica en vivo los supuestos del modulo IDEAM. Correr ANTES de la carga.

Resuelve los `TODO VERIFICAR` de src/acquisition/ideam.py:
  1. nombres exactos de los departamentos (con tilde)
  2. que la consulta agregada por departamento-anio responda y cuanto tarda
  3. intervalo real entre lecturas por codigo de sensor

Uso:
    python scripts/probe_ideam.py
Pegar la salida en docs/verificacion_api.md.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.acquisition import ideam
from src.common.http import sesion


def main() -> None:
    ses = sesion()
    for variable, meta in ideam.VARIABLES.items():
        print(f"\n=== {variable} ({meta['dataset']}) ===")
        print("actualizado:", ideam.fecha_actualizacion(meta["dataset"], ses))

        url = f"{ideam.BASE}/resource/{meta['dataset']}.json"
        r = ses.get(url, params={"$select": "departamento, count(*) AS n",
                                 "$group": "departamento", "$order": "departamento",
                                 "$where": "fechaobservacion >= '2026-01-01T00:00:00'"},
                    timeout=300)
        r.raise_for_status()
        publicados = {f["departamento"].upper() for f in r.json()}
        for depto in ideam.departamentos():
            nombre = ideam.NOMBRE_IDEAM.get(depto, depto)
            existe = nombre.upper() in publicados
            print(f"  {depto:20} -> {nombre:20} {'OK' if existe else 'NO EXISTE'}")

        inicio = time.monotonic()
        r = ses.get(url, params=ideam.consulta_mensual("BOYACÁ", 2026, 1), timeout=90)
        r.raise_for_status()
        agregado = r.json()
        print(f"  agregado BOYACÁ 2026-01: {len(agregado)} filas en {time.monotonic() - inicio:.1f} s")
        if agregado:
            print("  ejemplo:", agregado[0])

            estacion = max(agregado, key=lambda f: int(f["n_lecturas"]))["codigoestacion"]
            r = ses.get(url, params=ideam.consulta_muestra(estacion, "2026-09-01T00:00:00", 500),
                        timeout=120)
            muestra = pd.DataFrame(r.json())
            if not muestra.empty:
                muestra["t"] = pd.to_datetime(muestra["fechaobservacion"])
                for sensor, g in muestra.groupby("codigosensor"):
                    paso = g["t"].sort_values().diff().dropna().dt.total_seconds().div(60)
                    print(f"  estacion {estacion} sensor {sensor} "
                          f"({g['descripcionsensor'].iloc[0]}): intervalo mediano "
                          f"{paso.median():.0f} min, resolucion minima distinta de 0: "
                          f"{pd.to_numeric(g['valorobservado']).replace(0, pd.NA).min()}")


if __name__ == "__main__":
    main()
