"""Limpieza de las fuentes complementarias: NASA POWER, ONI y Pink Sheet.

Las tres son chicas y de estructura simple, por eso comparten modulo. Cada una
termina en formato largo (una fila por periodo y variable), que es el que
necesitan los hechos del modelo estrella.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path

import pandas as pd

from src.acquisition.nasa_power import a_filas, zonas
from src.acquisition.oni import leer as leer_oni
from src.common.rutas import ultima_carpeta_cruda

log = logging.getLogger(__name__)


# --- NASA POWER -------------------------------------------------------------

def limpiar_clima(carpeta: Path | None = None) -> pd.DataFrame:
    """Une los JSON de todas las zonas en una sola tabla larga."""
    carpeta = carpeta or ultima_carpeta_cruda("nasa_power")
    indice = {
        f"{z['producto']}_{z['departamento']}".replace(" ", "_"): z for z in zonas()
    }

    filas: list[dict] = []
    for archivo in sorted(carpeta.glob("*.json")):
        zona = indice.get(archivo.stem)
        if zona is None:
            log.warning("archivo sin zona declarada en config: %s", archivo.name)
            continue
        respuesta = json.loads(archivo.read_text(encoding="utf-8"))
        # La elevacion que POWER asigna a la celda de grilla, no la real del
        # municipio. En Colombia difieren mucho (a Villavicencio, a 467 m, le
        # asigna 1392 m) porque la grilla promedia el relieve. Se guarda como
        # columna para que el sesgo quede a la vista en el analisis.
        elevacion = respuesta["geometry"]["coordinates"][2]
        for fila in a_filas(respuesta, zona):
            fila["elevacion_grilla_m"] = elevacion
            filas.append(fila)

    df = pd.DataFrame(filas)
    if df.empty:
        return df
    # Una columna por parametro es mas comodo para calcular anomalias.
    return df.pivot_table(
        index=["producto", "departamento", "lat", "lon", "elevacion_grilla_m", "anio", "mes"],
        columns="parametro",
        values="valor",
    ).reset_index().rename_axis(None, axis=1)


def anomalia_precipitacion(df: pd.DataFrame, columna: str = "PRECTOTCORR") -> pd.DataFrame:
    """Agrega la desviacion de cada mes frente a su promedio historico del mismo mes.

    Comparar septiembre contra el promedio anual no dice nada en un pais con
    dos temporadas de lluvia. Hay que comparar septiembre contra septiembre.
    """
    if df.empty or columna not in df:
        return df
    base = df.groupby(["producto", "departamento", "mes"])[columna].transform("mean")
    df = df.copy()
    df[f"{columna}_anomalia"] = (df[columna] - base).round(3)
    return df


# --- ONI --------------------------------------------------------------------

def limpiar_enso(ruta: Path | None = None) -> pd.DataFrame:
    """Serie ONI con fase y marca de provisional."""
    ruta = ruta or ultima_carpeta_cruda("oni") / "oni.ascii.txt"
    return pd.DataFrame(leer_oni(ruta.read_text(encoding="utf-8")))


# --- Pink Sheet -------------------------------------------------------------

# En la hoja mensual: fila 5 los commodities, fila 6 las unidades, datos desde
# la 7 (numeracion de Excel, base 1). Los faltantes vienen como puntos
# suspensivos, no como celda vacia.
FILA_COMMODITIES = 4
FILA_UNIDADES = 5
PRIMERA_FILA_DATOS = 6
FALTANTE = "…"

_PERIODO = re.compile(r"^(\d{4})M(\d{1,2})$")
_ACTUALIZADO = re.compile(r"Updated on (.+)", re.IGNORECASE)


def fecha_publicacion(ruta: Path) -> str | None:
    """Fecha que el propio Excel declara en su encabezado ('Updated on ...')."""
    cabecera = pd.read_excel(ruta, sheet_name="Monthly Prices", nrows=4, header=None)
    for valor in cabecera.iloc[:, 0].dropna().astype(str):
        hallazgo = _ACTUALIZADO.search(valor)
        if hallazgo:
            return hallazgo.group(1).strip()
    return None


def limpiar_insumos(ruta: Path | None = None) -> pd.DataFrame:
    """Convierte la hoja mensual a formato largo (anio, mes, commodity, unidad, valor)."""
    if ruta is None:
        carpeta = ultima_carpeta_cruda("pink_sheet")
        candidatos = sorted(carpeta.glob("*.xlsx"))
        if not candidatos:
            raise FileNotFoundError(f"no hay xlsx en {carpeta}")
        ruta = candidatos[0]

    crudo = pd.read_excel(ruta, sheet_name="Monthly Prices", header=None)
    commodities = crudo.iloc[FILA_COMMODITIES].tolist()
    unidades = crudo.iloc[FILA_UNIDADES].tolist()
    datos = crudo.iloc[PRIMERA_FILA_DATOS:].reset_index(drop=True)

    filas: list[dict] = []
    for _, fila in datos.iterrows():
        periodo = _PERIODO.match(str(fila.iloc[0]).strip())
        if not periodo:
            continue
        anio, mes = int(periodo.group(1)), int(periodo.group(2))
        for col in range(1, len(commodities)):
            nombre = commodities[col]
            if not isinstance(nombre, str) or not nombre.strip():
                continue
            valor = fila.iloc[col]
            if isinstance(valor, str) and FALTANTE in valor:
                valor = None
            filas.append(
                {
                    "anio": anio,
                    "mes": mes,
                    "commodity": nombre.strip(),
                    "unidad": str(unidades[col]).strip() if isinstance(unidades[col], str) else None,
                    "valor_usd": pd.to_numeric(valor, errors="coerce"),
                }
            )
    return pd.DataFrame(filas)
