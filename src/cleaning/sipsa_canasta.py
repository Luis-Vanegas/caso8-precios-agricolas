"""Limpieza de las fuentes nuevas de SIPSA: precios semanales y abastecimiento.

Reglas que vienen de la investigacion del 2026-10-09 (ver la seccion
"Jerarquia de productos y unidades" de `docs/contrato_datos.md`):

- La llave del articulo es `art_id` (el artiId del DANE), nunca el nombre.
- La llave del mercado es `fuen_id`: hay mercados con dos nombres
  ("Cali, Santa Elena" y "Cali, Santa Helena" son el mismo, codigo 48).
- El precio va por kg, salvo huevo y bocadillo (por unidad) y aceite, jugo y
  vinagre (por litro), aunque el campo de la API se llame `promedioKg`.
- Nunca se promedian articulos distintos: cada fila es un articulo.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from src.acquisition import sipsa
from src.common.rutas import CONFIG, CRUDO, carpetas_con_datos

log = logging.getLogger(__name__)

# Metodologia SIPSA-P, p. 16. Se compara contra el inicio del nombre en minusculas.
POR_UNIDAD = ("huevo", "bocadillo")
POR_LITRO = ("aceite", "jugo de frutas", "vinagre")


def unidad(articulo: pd.Series) -> pd.Series:
    """Unidad del precio de cada articulo: 'kg', 'unidad' o 'litro'."""
    nombre = articulo.str.lower()
    salida = pd.Series("kg", index=articulo.index)
    salida[nombre.str.startswith(POR_UNIDAD)] = "unidad"
    salida[nombre.str.startswith(POR_LITRO)] = "litro"
    return salida


def cargar_mercados() -> pd.DataFrame:
    """Mercado -> ciudad, departamento y codigo DANE. Generado el 2026-10-09 a
    partir de los nombres del DANE ("Ciudad, Mercado" o "Municipio (Depto)")."""
    return pd.read_csv(CONFIG / "mercados_sipsa.csv", dtype={"dpto_codigo": str})


def _con_catalogo(df: pd.DataFrame) -> pd.DataFrame:
    """Pega producto y grupo DANE desde el catalogo homologado (tarea de Claude 2).

    Mientras el catalogo no exista, las columnas van vacias: el contrato lo permite.
    """
    ruta = CONFIG / "catalogo_articulos.csv"
    columnas = ["producto", "grupo_dane", "en_canasta"]
    if not ruta.exists():
        return df.assign(**{c: pd.NA for c in columnas})
    catalogo = pd.read_csv(ruta)[["art_id", *columnas]]
    # En el CSV va "si"/"no" (legible al editarlo en OpenRefine); el contrato pide booleano
    catalogo["en_canasta"] = catalogo["en_canasta"].eq("si")
    salida = df.merge(catalogo, on="art_id", how="left")
    nuevos = salida.loc[salida["producto"].isna(), "articulo"].unique()
    if len(nuevos):
        # El DANE agrega articulos: hay que homologarlos en el catalogo
        log.warning("articulos sin homologar en config/catalogo_articulos.csv: %s", list(nuevos)[:10])
    salida["en_canasta"] = salida["en_canasta"].fillna(False).astype(bool)
    return salida


def _con_mercado(df: pd.DataFrame) -> pd.DataFrame:
    """Pega ciudad y departamento por codigo de mercado y avisa si aparece uno nuevo."""
    salida = df.merge(cargar_mercados(), on="fuen_id", how="left")
    nuevos = salida.loc[salida["dpto_codigo"].isna(), "fuen_id"].unique()
    if len(nuevos):
        log.warning("mercados sin ubicar en config/mercados_sipsa.csv: %s", list(nuevos))
    return salida


def _registros(archivo: Path) -> pd.DataFrame:
    return pd.DataFrame(sipsa.leer_registros(archivo))


# --- Precios semanales --------------------------------------------------------

def unir_fotos(fotos: list[pd.DataFrame]) -> pd.DataFrame:
    """Une las descargas de varios dias. Si una misma semana sale en dos fotos,
    gana la descarga mas reciente (el DANE pudo corregir el dato)."""
    todo = pd.concat(fotos, ignore_index=True).sort_values("descarga", kind="stable")
    # El propio DANE a veces repite articulo-mercado-semana con dos precios
    # distintos en UNA misma descarga (2 casos el 2026-10-09, aguacates en
    # Tibasosa). Queda el ultimo que llega, pero se avisa en vez de callarlo.
    repetidos = todo.duplicated(["art_id", "fuen_id", "semana_inicio", "descarga"]).sum()
    if repetidos:
        log.warning("sipsa_semanal: %d filas repetidas dentro de una misma descarga del DANE", repetidos)
    return todo.drop_duplicates(["art_id", "fuen_id", "semana_inicio"], keep="last").reset_index(drop=True)


def limpiar_semanal(base: Path | None = None) -> pd.DataFrame:
    """Une TODAS las descargas guardadas: el servicio solo da 12 meses, la
    historia sale de acumular las fotos de cada dia."""
    base = base or CRUDO / "sipsa_semanal"
    fotos = []
    for carpeta in carpetas_con_datos(base):
        crudo = _registros(carpeta / "promediosSipsaSemanaMadr.xml")
        fotos.append(pd.DataFrame({
            "art_id": crudo["artiId"].astype(int),
            "articulo": crudo["artiNombre"].str.strip(),
            "fuen_id": crudo["fuenId"].astype(int),
            "semana_inicio": pd.to_datetime(crudo["fechaIni"].str[:10]),
            "precio": pd.to_numeric(crudo["promedioKg"]),
            "precio_min": pd.to_numeric(crudo["minimoKg"]),
            "precio_max": pd.to_numeric(crudo["maximoKg"]),
            "descarga": carpeta.name,
        }))
    if not fotos:
        raise FileNotFoundError(f"no hay descargas en {base}")

    df = unir_fotos(fotos).drop(columns="descarga")
    df["unidad"] = unidad(df["articulo"])
    df["anio"] = df["semana_inicio"].dt.year
    df["mes"] = df["semana_inicio"].dt.month
    df["periodo"] = df["anio"] * 100 + df["mes"]
    return _con_catalogo(_con_mercado(df))


# --- Abastecimiento -----------------------------------------------------------

def limpiar_abastecimiento(base: Path | None = None) -> pd.DataFrame:
    """Toneladas por articulo, mercado y mes. El servicio trae toda la historia,
    asi que basta la descarga mas reciente."""
    base = base or CRUDO / "sipsa_abastecimiento"
    carpetas = carpetas_con_datos(base)
    if not carpetas:
        raise FileNotFoundError(f"no hay descargas en {base}")
    crudo = _registros(carpetas[-1] / "promedioAbasSipsaMesMadr.xml")

    fecha = pd.to_datetime(crudo["fechaMesIni"].str[:10])
    df = pd.DataFrame({
        "art_id": crudo["artiId"].astype(int),
        "articulo": crudo["artiNombre"].str.strip(),
        "fuen_id": crudo["fuenId"].astype(int),
        "anio": fecha.dt.year,
        "mes": fecha.dt.month,
        "toneladas": pd.to_numeric(crudo["cantidadTon"]),
    })
    df["periodo"] = df["anio"] * 100 + df["mes"]
    return _con_catalogo(_con_mercado(df))
