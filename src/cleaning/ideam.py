"""Limpieza de los agregados mensuales del IDEAM.

Tres decisiones, cada una con su razon:

1. **Completitud relativa y no absoluta.** No se asume cuantas lecturas deberia
   tener un mes (144 por dia si el sensor fuera de 10 minutos), porque la
   frecuencia real por codigo de sensor esta por verificar. Se compara cada mes
   contra la mediana de lecturas mensuales de esa misma estacion y sensor. Un
   mes con la mitad de lecturas de lo normal tiene la lluvia subestimada.

2. **Rangos fisicos.** Lluvia negativa o temperatura fuera de [-10, 45] °C en
   Colombia continental no es clima, es falla del sensor. El mes se marca, no
   se corrige.

3. **Mediana entre estaciones.** El valor del departamento es la mediana de sus
   estaciones validas: una estacion con un sensor descalibrado no arrastra el
   dato del departamento como lo haria un promedio.
"""

from __future__ import annotations

import json
import logging
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

from src.acquisition.ideam import NOMBRE_IDEAM
from src.common.rutas import CRUDO, archivos_mas_recientes

log = logging.getLogger(__name__)

COMPLETITUD_MINIMA = 0.8
RANGO_FISICO = {
    "precipitacion": (0.0, None),
    "temperatura": (-10.0, 45.0),
}


def sin_tilde(texto: str) -> str:
    """'Boyacá' -> 'Boyaca'. Deja el departamento en el vocabulario de config."""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    )


# {'BOYACA': 'Boyaca', 'NORTE DE SANTANDER': 'Norte de Santander', ...}: nombre de config por clave sin tilde y en mayusculas.
_CANONICO = {sin_tilde(nombre).upper(): nombre for nombre in NOMBRE_IDEAM}


def a_vocabulario_config(texto: str) -> str:
    """'BOYACA' o 'Boyacá' -> 'Boyaca' (el nombre que usa config/zonas_productoras.json).

    IDEAM publica cada departamento con dos convenciones de mayusculas que se
    reparten el tiempo. Si solo se le quitara la tilde, 'BOYACA' y 'Boyaca'
    quedarian como dos departamentos distintos y cada serie saldria partida.
    """
    return _CANONICO.get(sin_tilde(texto).upper(), sin_tilde(texto))


def leer(carpeta: Path | None = None) -> pd.DataFrame:
    """Une los JSON agregados. La variable sale del nombre del archivo.

    Sin `carpeta`, toma la version mas reciente de CADA archivo entre todas las
    descargas: si hoy fallo uno, se usa su ultima copia buena (ver
    `archivos_mas_recientes`).
    """
    if carpeta:
        archivos = sorted(carpeta.glob("*_*_*.json"))
    else:
        archivos = archivos_mas_recientes(CRUDO / "ideam", "*_*_*.json")
        ultima = max(a.parent for a in archivos) if archivos else None
        viejos = [a.name for a in archivos if a.parent != ultima]
        if viejos:
            log.warning("ideam: %d archivos vienen de una descarga anterior (fallaron en la ultima): %s",
                        len(viejos), viejos[:5])
    partes = []
    for archivo in archivos:
        variable = archivo.stem.split("_")[0]
        filas = json.loads(archivo.read_text(encoding="utf-8"))
        if filas:
            df = pd.DataFrame(filas)
            df["variable"] = variable
            partes.append(df)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def limpiar(crudo: pd.DataFrame) -> pd.DataFrame:
    """Tipa, calcula completitud y marca meses fuera de rango. Grano: estacion-sensor-mes."""
    if crudo.empty:
        return crudo
    df = crudo.copy()
    for col in ("suma", "promedio", "minimo", "maximo", "latitud", "longitud"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df["n_lecturas"] = pd.to_numeric(df["n_lecturas"], errors="coerce").astype("Int64")
    fecha = pd.to_datetime(df.pop("mes"))
    df["anio"], df["mes"] = fecha.dt.year, fecha.dt.month
    df["departamento"] = df["departamento"].map(a_vocabulario_config)

    llave = ["variable", "codigoestacion", "codigosensor"]
    tipico = df.groupby(llave)["n_lecturas"].transform("median")
    df["completitud"] = (df["n_lecturas"] / tipico).clip(upper=1.0).round(3)

    df["fuera_de_rango"] = False
    for variable, (bajo, alto) in RANGO_FISICO.items():
        es = df["variable"] == variable
        if bajo is not None:
            df.loc[es & (df["minimo"] < bajo), "fuera_de_rango"] = True
        if alto is not None:
            df.loc[es & (df["maximo"] > alto), "fuera_de_rango"] = True

    df["valido"] = (df["completitud"] >= COMPLETITUD_MINIMA) & ~df["fuera_de_rango"]
    # El valor fisico del mes: lluvia acumulada o temperatura media.
    df["valor"] = np.where(df["variable"] == "precipitacion", df["suma"], df["promedio"])
    return df.drop_duplicates(subset=llave + ["anio", "mes"])


def a_departamento(estaciones: pd.DataFrame) -> pd.DataFrame:
    """Mediana de las estaciones validas por departamento y mes, con su anomalia.

    La anomalia compara cada mes contra el promedio del mismo mes calendario en
    ese departamento, igual que con NASA POWER, para que los dos indicadores de
    clima se lean en la misma escala.
    """
    validas = estaciones[estaciones["valido"]]
    if validas.empty:
        return pd.DataFrame()
    depto = (
        validas.groupby(["variable", "departamento", "anio", "mes"])
        .agg(valor=("valor", "median"), n_estaciones=("codigoestacion", "nunique"))
        .reset_index()
    )
    normal = depto.groupby(["variable", "departamento", "mes"])["valor"].transform("mean")
    depto["anomalia"] = (depto["valor"] - normal).round(3)
    return depto
