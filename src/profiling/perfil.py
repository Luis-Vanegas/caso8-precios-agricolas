"""Perfilado: describe cada tabla y busca inconsistencias antes de integrar.

Perfilar no es imprimir `df.describe()`. Es responder tres preguntas concretas:
que falta, que se repite y que es imposible. Lo tercero es lo que mas sirve y
lo que casi nadie hace.
"""

from __future__ import annotations

import pandas as pd


def perfilar(df: pd.DataFrame, nombre: str) -> pd.DataFrame:
    """Una fila por columna: tipo, nulos, unicos y rango."""
    filas = []
    for col in df.columns:
        serie = df[col]
        nulos = int(serie.isna().sum())
        fila = {
            "tabla": nombre,
            "columna": col,
            "tipo": str(serie.dtype),
            "filas": len(serie),
            "nulos": nulos,
            "pct_nulos": round(100 * nulos / len(serie), 2) if len(serie) else 0.0,
            "unicos": int(serie.nunique(dropna=True)),
            "minimo": None,
            "maximo": None,
        }
        if pd.api.types.is_numeric_dtype(serie) and serie.notna().any():
            fila["minimo"] = serie.min()
            fila["maximo"] = serie.max()
        filas.append(fila)
    return pd.DataFrame(filas)


def duplicados(df: pd.DataFrame, claves: list[str]) -> int:
    """Cuantas filas repiten la combinacion de claves que deberia ser unica."""
    presentes = [c for c in claves if c in df.columns]
    if not presentes:
        return 0
    return int(df.duplicated(subset=presentes).sum())


def negativos(df: pd.DataFrame, columna: str) -> int:
    """Valores negativos donde no pueden existir (precios, cantidades, areas)."""
    if columna not in df.columns:
        return 0
    return int((df[columna] < 0).sum())


def comercio_imposible(df_comercio: pd.DataFrame, df_produccion: pd.DataFrame) -> pd.DataFrame:
    """Casos donde las exportaciones superan produccion mas importaciones.

    Puede ser reexportacion legitima o error de la fuente. No se corrige aca: se
    reporta para que quede documentado en el analisis.

    Dos filtros que hacen la diferencia entre un hallazgo y un falso positivo:

    1. Solo filas en toneladas. Produccion y comercio tambien traen cabezas de
       animal ('An', '1000 No') y sumar unidades distintas no significa nada.
    2. Solo items que existen en produccion Y en comercio. El dominio de
       comercio incluye agregados de grupo ('Fruit', codigo 1802) y productos
       procesados ('Apple juice') que por definicion no tienen fila de
       produccion primaria. Compararlos contra cero marca miles de casos falsos.

    Devuelve tambien, en el atributo `attrs`, cuantos item-anio quedaron fuera
    por no ser comparables.
    """
    exportado = _pivote(df_comercio, "Export quantity", "exportado")
    importado = _pivote(df_comercio, "Import quantity", "importado")
    producido = _pivote(df_produccion, "Production", "producido")

    comerciados = set(exportado["item"]) | set(importado["item"])
    comparables = set(producido["item"]) & comerciados

    cruce = producido.merge(importado, on=["item", "anio"], how="outer").merge(
        exportado, on=["item", "anio"], how="outer"
    )
    for col in ("producido", "importado", "exportado"):
        cruce[col] = cruce[col].fillna(0)

    fuera = cruce[~cruce["item"].isin(comparables)]
    cruce = cruce[cruce["item"].isin(comparables)]

    cruce["disponible"] = cruce["producido"] + cruce["importado"]
    resultado = cruce[cruce["exportado"] > cruce["disponible"]].sort_values(
        "exportado", ascending=False
    )
    resultado.attrs["no_comparables"] = len(fuera)
    resultado.attrs["items_no_comparables"] = len(comerciados - comparables)
    return resultado


UNIDAD_MASA = "t"


def _pivote(df: pd.DataFrame, elemento: str, nombre: str, unidad: str = UNIDAD_MASA) -> pd.DataFrame:
    """Suma el valor de un elemento por item y anio, dentro de una sola unidad."""
    if df.empty or "elemento" not in df.columns:
        return pd.DataFrame(columns=["item", "anio", nombre])
    sub = df[(df["elemento"] == elemento) & (df["unidad"] == unidad)]
    return (
        sub.groupby(["item", "anio"], dropna=False)["valor"]
        .sum()
        .reset_index()
        .rename(columns={"valor": nombre})
    )


def huecos_de_serie(df: pd.DataFrame, claves: list[str], columna_tiempo: str) -> pd.DataFrame:
    """Cuenta periodos faltantes dentro del rango de cada serie.

    Sirve para decidir que hueco se interpola y cual se deja vacio: un hueco de
    un mes se puede rellenar, uno de cinco anios no.
    """
    resultado = []
    for llave, grupo in df.groupby(claves, dropna=False):
        periodos = grupo[columna_tiempo].dropna().astype(int)
        if periodos.empty:
            continue
        esperados = set(range(periodos.min(), periodos.max() + 1))
        faltan = sorted(esperados - set(periodos))
        if faltan:
            resultado.append(
                {
                    "serie": llave if isinstance(llave, tuple) else (llave,),
                    "desde": periodos.min(),
                    "hasta": periodos.max(),
                    "faltantes": len(faltan),
                    "hueco_mayor": _hueco_mayor(faltan),
                }
            )
    return pd.DataFrame(resultado)


def _hueco_mayor(faltantes: list[int]) -> int:
    """Longitud del tramo consecutivo mas largo de periodos ausentes."""
    if not faltantes:
        return 0
    mayor = actual = 1
    for previo, siguiente in zip(faltantes, faltantes[1:]):
        actual = actual + 1 if siguiente == previo + 1 else 1
        mayor = max(mayor, actual)
    return mayor
