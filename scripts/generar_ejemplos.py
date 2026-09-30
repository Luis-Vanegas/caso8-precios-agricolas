"""Extrae muestras pequenas y REALES de los datos para la pagina "Recorrido paso a paso".

La app no puede leer data/raw ni data/interim (no se suben a GitHub), asi que se
guardan unas pocas filas en app/ejemplos/. Correr despues de preparar.py:

    python scripts/generar_ejemplos.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.rutas import INTERMEDIO, RAIZ, ultima_carpeta_cruda

SALIDA = RAIZ / "app" / "ejemplos"


def sipsa_diario() -> None:
    """Precios diarios de papa negra en Bogota en agosto de 2026 (antes de pasar a mes)."""
    d = pd.read_parquet(INTERMEDIO / "sipsa" / "sipsa_diario.parquet",
                        columns=["fecha", "mercado", "producto", "precio_cop_kg"])
    d["fecha"] = pd.to_datetime(d["fecha"])
    m = d[(d["producto"] == "Papa negra*") & (d["mercado"] == "BOGOTÁ, D.C.")
          & (d["fecha"].dt.year == 2026) & (d["fecha"].dt.month == 8)]
    m.sort_values("fecha").to_csv(SALIDA / "sipsa_diario_papa_bogota_2026_08.csv", index=False)


def faostat_crudo() -> None:
    """Tres filas del CSV original de FAOSTAT (produccion de papa en Colombia)."""
    zip_ = ultima_carpeta_cruda("faostat_bulk") / "Production_Crops_Livestock_E_All_Data_(Normalized).zip"
    with zipfile.ZipFile(zip_) as z:
        nombre = next(n for n in z.namelist() if n.endswith("(Normalized).csv"))
        with z.open(nombre) as f:
            for bloque in pd.read_csv(f, encoding="latin-1", chunksize=200_000):
                sel = bloque[(bloque["Area"] == "Colombia") & (bloque["Item"] == "Potatoes")
                             & (bloque["Year"] >= 2022)]
                if not sel.empty:
                    sel.head(6).to_csv(SALIDA / "faostat_crudo_papa_colombia.csv", index=False)
                    return


if __name__ == "__main__":
    SALIDA.mkdir(parents=True, exist_ok=True)
    sipsa_diario()
    faostat_crudo()
    for f in sorted(SALIDA.glob("*.csv")):
        print(f.name, len(pd.read_csv(f)), "filas")
