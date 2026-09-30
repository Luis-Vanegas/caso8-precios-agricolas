"""Limpieza de SIPSA: del volcado SOAP a una tabla de precios mayoristas.

Campos crudos (verificados en Fase 0): ciudad, codProducto, enviado,
fechaCaptura, fechaCreacion, precioPromedio, producto, regId.

`precioPromedio` esta en pesos colombianos por kilogramo. La guia del DANE lo
describe como cantidad, pero los valores solo tienen sentido como precio.
Pendiente de validar contra un boletin publicado (ver TASKS.md).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.acquisition.sipsa import leer_registros
from src.common.rutas import ultima_carpeta_cruda

log = logging.getLogger(__name__)

# El asterisco marca variedades en el catalogo del DANE. Se guarda aparte en vez
# de borrarlo: distingue "Guayaba*" de "Guayaba" y esa diferencia es informacion.
SUFIJO_VARIEDAD = "*"

# Mercados que el DANE renombro. Sin unificarlos, la serie se parte en dos y el
# z-score de la alerta arranca de cero en la mitad de la historia.
# Verificado en los datos: "CÚCUTA" publica hasta 2022-12-02 y
# "SAN JOSÉ DE CÚCUTA" desde 2022-12-06, con los mismos productos.
MERCADOS_RENOMBRADOS = {
    "CÚCUTA": "SAN JOSÉ DE CÚCUTA",
}


def normalizar_mercado(mercado: pd.Series) -> pd.Series:
    """Mayusculas, sin espacios sobrantes y con los renombres del DANE unificados."""
    return mercado.str.strip().str.upper().replace(MERCADOS_RENOMBRADOS)


def limpiar(ruta: Path | None = None) -> pd.DataFrame:
    """Lee el volcado crudo y devuelve la tabla tipada."""
    if ruta is None:
        ruta = ultima_carpeta_cruda("sipsa") / "promediosSipsaCiudad.xml"
    df = pd.DataFrame(leer_registros(ruta))
    if df.empty:
        return df

    df = df.rename(
        columns={
            "ciudad": "mercado",
            "codProducto": "producto_codigo",
            "fechaCaptura": "fecha",
            "fechaCreacion": "fecha_creacion",
            "precioPromedio": "precio_cop_kg",
            "producto": "producto",
            "regId": "registro_id",
        }
    )

    df["precio_cop_kg"] = pd.to_numeric(df["precio_cop_kg"], errors="coerce")
    df["producto_codigo"] = pd.to_numeric(df["producto_codigo"], errors="coerce").astype("Int64")
    df["registro_id"] = pd.to_numeric(df["registro_id"], errors="coerce").astype("Int64")
    # Las fechas traen huso -05:00; se normalizan a fecha sin hora.
    df["fecha"] = pd.to_datetime(df["fecha"], format="ISO8601", utc=True).dt.date
    df["fecha_creacion"] = pd.to_datetime(df["fecha_creacion"], format="ISO8601", utc=True)

    df["mercado"] = normalizar_mercado(df["mercado"])
    df["producto"] = df["producto"].str.strip()
    df["es_variedad"] = df["producto"].str.endswith(SUFIJO_VARIEDAD)
    df["producto_base"] = df["producto"].str.rstrip(SUFIJO_VARIEDAD).str.strip()

    df["anio"] = pd.to_datetime(df["fecha"]).dt.year
    df["mes"] = pd.to_datetime(df["fecha"]).dt.month

    return df.drop(columns=["enviado"], errors="ignore")


def a_mensual(df: pd.DataFrame) -> pd.DataFrame:
    """Promedio mensual por mercado y producto.

    Los precios de SIPSA son diarios; los de FAOSTAT son anuales y mensuales.
    Para cruzarlos hay que llevarlos a la misma frecuencia.
    """
    if df.empty:
        return df
    agrupado = (
        df.groupby(["mercado", "producto", "producto_codigo", "anio", "mes"], dropna=False)
        .agg(
            precio_cop_kg=("precio_cop_kg", "mean"),
            dias_con_dato=("precio_cop_kg", "count"),
            precio_min=("precio_cop_kg", "min"),
            precio_max=("precio_cop_kg", "max"),
        )
        .reset_index()
    )
    agrupado["precio_cop_kg"] = agrupado["precio_cop_kg"].round(2)

    # El mes de la ultima fecha publicada sigue abierto: tiene menos dias que un
    # mes normal y su promedio todavia puede cambiar. Se marca para que la app
    # no dispare alertas sobre un mes a medias.
    ultima = pd.to_datetime(df["fecha"]).max()
    periodo = agrupado["anio"] * 100 + agrupado["mes"]
    agrupado["mes_cerrado"] = periodo < ultima.year * 100 + ultima.month
    return agrupado
