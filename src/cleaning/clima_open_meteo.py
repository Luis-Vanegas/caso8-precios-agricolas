"""Limpieza de Open-Meteo: clima diario (observado + pronostico) y estacional mensual.

Los archivos crudos se llaman `<tipo>_<Departamento>.json` (ver
`src/acquisition/open_meteo.py`), con espacios cambiados por guion bajo.
"""

from __future__ import annotations

import calendar
import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.common.rutas import CONFIG, CRUDO, archivos_mas_recientes

COLUMNAS_ESTACIONAL = ["departamento", "dpto_codigo", "anio", "mes", "periodo",
                       "precip_p10", "precip_p50", "precip_p90", "anomalia_p50"]


def _codigos() -> dict[str, str]:
    """Departamento -> codigo DANE de 2 digitos."""
    dep = pd.read_csv(CONFIG / "departamentos.csv", dtype=str)
    return dict(zip(dep["departamento"], dep["dpto_codigo"]))


def _archivos(base: Path, tipo: str):
    """(departamento, contenido) de cada archivo de un tipo. Se toma la version mas
    reciente de cada departamento: si hoy fallo uno, se usa su ultima copia buena."""
    archivos = archivos_mas_recientes(base, f"{tipo}_*.json")
    if not archivos and tipo == "observado":
        raise FileNotFoundError(f"no hay descargas de Open-Meteo en {base}")
    for ruta in archivos:
        departamento = ruta.stem.removeprefix(f"{tipo}_").replace("_", " ")
        yield departamento, json.loads(ruta.read_text(encoding="utf-8"))


# --- Diario ---------------------------------------------------------------------

def limpiar_diario(base: Path | None = None) -> pd.DataFrame:
    """Una fila por departamento y dia, marcada `observado` o `pronostico`."""
    base = base or CRUDO / "open_meteo"
    partes = []
    for tipo in ("observado", "pronostico"):
        for departamento, datos in _archivos(base, tipo):
            d = datos["daily"]
            partes.append(pd.DataFrame({
                "departamento": departamento,
                "fecha": pd.to_datetime(d["time"]),
                "precipitacion_mm": d["precipitation_sum"],
                "temp_max": d["temperature_2m_max"],
                "temp_min": d["temperature_2m_min"],
                "tipo": tipo,
            }))
    df = pd.concat(partes, ignore_index=True)
    # Si un dia aparece observado y pronosticado, gana lo observado (va primero)
    df = df.drop_duplicates(["departamento", "fecha"], keep="first")
    df["dpto_codigo"] = df["departamento"].map(_codigos())
    df["fuente"] = "open-meteo"
    return df


# --- Estacional -----------------------------------------------------------------

def estacional_mensual(respuesta: dict, departamento: str) -> pd.DataFrame:
    """Lluvia de cada mes futuro segun los escenarios del ensamble.

    Pasos:
      1. Cada escenario (serie base + miembros) se suma por mes.
      2. Solo cuentan los meses COMPLETOS: todos sus dias presentes y sin vacios
         en ningun escenario. Un mes a medias subestimaria la lluvia.
      3. De los escenarios se sacan los percentiles 10, 50 y 90: el 50 es el
         escenario del medio y el 10-90 es el rango probable.
    """
    d = respuesta["daily"]
    escenarios = pd.DataFrame({k: v for k, v in d.items() if k.startswith("precipitation_sum")},
                              index=pd.to_datetime(d["time"]), dtype="float64")
    filas = []
    for (anio, mes), bloque in escenarios.groupby([escenarios.index.year, escenarios.index.month]):
        completo = len(bloque) == calendar.monthrange(anio, mes)[1] and not bloque.isna().any().any()
        if not completo:                                             # paso 2
            continue
        totales = bloque.sum().to_numpy()                            # paso 1
        p10, p50, p90 = np.percentile(totales, [10, 50, 90])         # paso 3
        filas.append({"departamento": departamento, "anio": anio, "mes": mes,
                      "periodo": anio * 100 + mes, "precip_p10": round(p10, 1),
                      "precip_p50": round(p50, 1), "precip_p90": round(p90, 1)})
    return pd.DataFrame(filas)


def climatologia(diario: pd.DataFrame) -> pd.DataFrame:
    """Lluvia promedio de cada mes del ano por departamento, con los meses
    observados completos (desde 2020). Es la referencia de "lo normal"."""
    obs = diario[diario["tipo"] == "observado"]
    mensual = (obs.groupby(["departamento", obs["fecha"].dt.year.rename("anio"),
                            obs["fecha"].dt.month.rename("mes")])
               .agg(lluvia=("precipitacion_mm", "sum"), dias=("precipitacion_mm", "count"))
               .reset_index())
    dias_del_mes = [calendar.monthrange(a, m)[1] for a, m in zip(mensual["anio"], mensual["mes"])]
    mensual = mensual[mensual["dias"] == dias_del_mes]
    return mensual.groupby(["departamento", "mes"], as_index=False)["lluvia"].mean().rename(
        columns={"lluvia": "lluvia_normal"})


def limpiar_estacional(base: Path | None = None) -> pd.DataFrame:
    """Pronostico estacional mensual por departamento, con su anomalia frente a lo normal."""
    base = base or CRUDO / "open_meteo"
    partes = [estacional_mensual(datos, depto) for depto, datos in _archivos(base, "estacional")]
    df = pd.concat([p for p in partes if not p.empty] or [pd.DataFrame(columns=COLUMNAS_ESTACIONAL)],
                   ignore_index=True)
    if df.empty:
        return df[COLUMNAS_ESTACIONAL]

    df["dpto_codigo"] = df["departamento"].map(_codigos())
    if archivos_mas_recientes(base, "observado_*.json"):
        normal = climatologia(limpiar_diario(base))
        df = df.merge(normal, on=["departamento", "mes"], how="left")
        df["anomalia_p50"] = (df["precip_p50"] - df["lluvia_normal"]).round(1)
    else:
        df["anomalia_p50"] = np.nan
    return df[COLUMNAS_ESTACIONAL]
