"""Homologacion de productos SIPSA contra items de FAOSTAT.

El mapeo vive en `config/homologacion_productos.csv`, no en el codigo: es una
decision de dominio que se revisa a mano y se versiona. Este modulo lo carga y
lo valida contra los datos reales.

La correspondencia NO es uno a uno, y esa es la conclusion importante:

  - `exacta`: el item de FAO representa el mismo producto.
  - `agregada`: FAO mete varios productos de SIPSA en un solo item. Guayaba y
    mango comparten el item 571; limon comun y Tahiti comparten el 497. El
    precio de FAO para ese item no es comparable con el de un solo producto.
  - `generica`: el producto cae en un cajon "n.e.c." junto con decenas de otros.
    Sirve para ubicarlo en la jerarquia, no para comparar precios.
  - `sin_equivalente`: FAO no publica ese producto para Colombia.
"""

from __future__ import annotations

import pandas as pd

from src.common.rutas import CONFIG

ARCHIVO = CONFIG / "homologacion_productos.csv"

# Solo las correspondencias exactas permiten comparar el precio mayorista de
# SIPSA contra el precio productor de FAO del mismo bien.
COMPARABLES = ("exacta",)

TIPOS_VALIDOS = {"exacta", "agregada", "generica", "sin_equivalente"}


def cargar() -> pd.DataFrame:
    """Lee el mapeo desde el CSV versionado."""
    df = pd.read_csv(ARCHIVO, encoding="utf-8", dtype={"item_codigo_fao": "Int64"})
    desconocidos = set(df["tipo_correspondencia"]) - TIPOS_VALIDOS
    if desconocidos:
        raise ValueError(f"tipo_correspondencia invalido: {sorted(desconocidos)}")
    return df


def validar(mapeo: pd.DataFrame, productos_sipsa: set[str], items_fao: set[int]) -> list[str]:
    """Devuelve la lista de problemas. Lista vacia significa mapeo consistente.

    Se chequea contra los datos reales para que el mapeo no se pudra en silencio
    cuando el DANE agregue un producto o FAO renombre un item.
    """
    problemas: list[str] = []

    faltan = productos_sipsa - set(mapeo["producto_sipsa"])
    if faltan:
        problemas.append(f"productos de SIPSA sin homologar: {sorted(faltan)}")

    sobran = set(mapeo["producto_sipsa"]) - productos_sipsa
    if sobran:
        problemas.append(f"el mapeo nombra productos que SIPSA ya no publica: {sorted(sobran)}")

    con_codigo = mapeo[mapeo["item_codigo_fao"].notna()]
    inexistentes = set(con_codigo["item_codigo_fao"]) - items_fao
    if inexistentes:
        problemas.append(f"codigos FAO que no existen para Colombia: {sorted(inexistentes)}")

    sin_codigo = mapeo[
        mapeo["item_codigo_fao"].isna() & (mapeo["tipo_correspondencia"] != "sin_equivalente")
    ]
    if not sin_codigo.empty:
        problemas.append(
            f"sin codigo FAO pero marcados como homologados: "
            f"{sorted(sin_codigo['producto_sipsa'])}"
        )

    return problemas


def resumen(mapeo: pd.DataFrame) -> pd.DataFrame:
    """Cuantos productos cayeron en cada tipo de correspondencia."""
    return (
        mapeo["tipo_correspondencia"]
        .value_counts()
        .rename_axis("tipo_correspondencia")
        .reset_index(name="productos")
    )


def colisiones(mapeo: pd.DataFrame) -> pd.DataFrame:
    """Items de FAO que reciben mas de un producto de SIPSA.

    Cada colision es un cruce que NO se puede hacer a nivel de producto: si
    guayaba y mango caen en el mismo item, el precio productor de ese item no
    corresponde a ninguno de los dos por separado.
    """
    con_codigo = mapeo[mapeo["item_codigo_fao"].notna()]
    conteo = con_codigo.groupby(["item_codigo_fao", "item_fao"])["producto_sipsa"].agg(
        ["count", lambda s: " + ".join(sorted(s))]
    )
    conteo.columns = ["productos_sipsa", "cuales"]
    return conteo[conteo["productos_sipsa"] > 1].reset_index()
