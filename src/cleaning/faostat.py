"""Limpieza de los seis dominios de FAOSTAT: filtra Colombia y normaliza columnas.

Los zip se leen por bloques sin descomprimirlos a disco. Trade pesa 267 MB
comprimidos y 17 millones de filas, de las cuales Colombia es una fraccion
minima: no tiene sentido materializar el resto.

Verificado en los archivos reales:
  - Colombia es `Area Code` 44, M49 '170.
  - La codificacion de los CSV es latin-1, no UTF-8.
  - `Months Code` 7021 es "Annual value"; los meses reales tienen otros codigos.
"""

from __future__ import annotations

import logging
import zipfile
from pathlib import Path

import pandas as pd

from src.common.rutas import ultima_carpeta_cruda

log = logging.getLogger(__name__)

AREA_COLOMBIA = 44
CODIFICACION = "latin-1"
BLOQUE = 500_000  # filas por lectura

# Codigo de "Months" que en realidad representa el agregado anual.
MESES_ANUAL = 7021

# Fragmento del nombre del zip por dominio. Se busca por fragmento porque el
# nombre trae el sufijo "(Normalized)" y puede variar.
ZIPS = {
    "PP": "Prices_E_All_Data",
    "QCL": "Production_Crops_Livestock_E_All_Data",
    "TCL": "Trade_CropsLivestock_E_All_Data",
    "FBS": "FoodBalanceSheets_E_All_Data",
    "QV": "Value_of_Production_E_All_Data",
    "PE": "Exchange_rate_E_All_Data",
}

# Nombres de columna en minusculas y sin espacios, para que OpenRefine y Power
# Query no peleen con "Area Code (M49)".
RENOMBRES = {
    "Area Code": "area_codigo",
    "Area Code (M49)": "area_m49",
    "Area": "area",
    "Item Code": "item_codigo",
    "Item Code (CPC)": "item_cpc",
    "Item Code (FBS)": "item_fbs",
    "Item": "item",
    "Element Code": "elemento_codigo",
    "Element": "elemento",
    "Year Code": "anio_codigo",
    "Year": "anio",
    "Months Code": "mes_codigo",
    "Months": "mes_nombre",
    "Unit": "unidad",
    "Value": "valor",
    "Flag": "flag",
    "Note": "nota",
    "ISO Currency Code": "moneda_iso",
    "Currency": "moneda",
}


def _ruta_zip(dominio: str, carpeta: Path) -> Path:
    fragmento = ZIPS[dominio]
    candidatos = [p for p in carpeta.glob("*.zip") if fragmento in p.name]
    if not candidatos:
        raise FileNotFoundError(f"no esta el zip de {dominio} en {carpeta}")
    return candidatos[0]


def extraer_colombia(dominio: str, carpeta: Path | None = None) -> pd.DataFrame:
    """Devuelve solo las filas de Colombia de un dominio, con columnas normalizadas."""
    carpeta = carpeta or ultima_carpeta_cruda("faostat_bulk")
    ruta = _ruta_zip(dominio, carpeta)

    with zipfile.ZipFile(ruta) as z:
        interno = [n for n in z.namelist() if "Normalized" in n][0]
        with z.open(interno) as handle:
            bloques = [
                bloque[bloque["Area Code"] == AREA_COLOMBIA]
                for bloque in pd.read_csv(
                    handle,
                    encoding=CODIFICACION,
                    chunksize=BLOQUE,
                    low_memory=False,
                )
            ]

    df = pd.concat(bloques, ignore_index=True) if bloques else pd.DataFrame()
    if df.empty:
        log.warning("%s no trajo filas de Colombia", dominio)
        return df

    df = df.rename(columns=RENOMBRES)
    df["dominio"] = dominio
    # El M49 viene con apostrofo inicial ("'170") para que Excel no lo lea como
    # numero. Aca estorba.
    if "area_m49" in df:
        df["area_m49"] = df["area_m49"].astype(str).str.lstrip("'")
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df["anio"] = pd.to_numeric(df["anio"], errors="coerce").astype("Int64")

    # Frecuencia explicita: sin esto, mezclar el agregado anual con los meses
    # duplica cada serie.
    if "mes_codigo" in df:
        df["frecuencia"] = (df["mes_codigo"] == MESES_ANUAL).map(
            {True: "anual", False: "mensual"}
        )
    else:
        df["frecuencia"] = "anual"

    return df
