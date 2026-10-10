"""Descargar datos: cualquier tabla de la base en CSV o Excel, lista para
OpenRefine o Power Query, sin instalar Python ni abrir DuckDB.

El CSV va en UTF-8 con BOM: asi Excel y Power Query leen bien las tildes.
"""

import io
import zipfile

import pandas as pd
import streamlit as st

import estilo
from datos import TTL, conexion

# Que es cada tabla, en una linea. Las que no esten aqui se listan igual.
DESCRIPCION = {
    "fact_precio_mayorista": "Precio mensual $/kg por producto y mercado (SIPSA). La tabla central.",
    "fact_precio_semanal": "Precio semanal por artículo (cada variedad por separado) y mercado.",
    "fact_abastecimiento": "Toneladas que llegan a cada central de abastos por mes.",
    "fact_clima": "Lluvia y temperatura mensual en las zonas productoras (NASA POWER + IDEAM).",
    "fact_clima_diario": "Clima diario por departamento: observado y pronóstico (Open-Meteo).",
    "fact_pronostico_estacional": "Lluvia esperada para los próximos meses (50 escenarios resumidos).",
    "fact_enso": "Índice El Niño / La Niña (ONI) por mes.",
    "fact_sensor_ideam": "Lluvia medida por estaciones del IDEAM.",
    "fact_precio_productor": "Precio al productor de la FAO (anual).",
    "fact_produccion": "Producción agrícola de la FAO (anual).",
    "fact_comercio": "Importaciones y exportaciones de la FAO (anual).",
    "dim_mercado": "Catálogo de mercados: ciudad, departamento y código DANE.",
    "dim_producto_sipsa": "Catálogo de productos SIPSA y su grupo.",
    "dim_tiempo": "Calendario: año, mes y si el mes ya cerró.",
    "puente_zona_sipsa": "Qué departamento produce cada producto (une precio con clima).",
    "indicador_sensibilidad_clima": "Resultado del análisis: cuánto mueve el clima a la oferta y al precio.",
    "indicador_quiebres": "Resultado de la prueba de Chow: si cambió el comportamiento de un precio.",
    "pronostico_precio": "Pronóstico a 1, 2 y 3 meses con su banda y su error contra el pasado.",
}
LIMITE_EXCEL = 200_000  # filas; mas que eso, Excel se vuelve lento: mejor el CSV


@st.cache_data(ttl=TTL)
def tablas() -> pd.DataFrame:
    """Tablas de la base con su numero de filas, primero las descritas."""
    con = conexion()
    nombres = [n for (n,) in con.execute(
        "SELECT table_name FROM information_schema.tables WHERE table_schema = 'main' ORDER BY 1").fetchall()]
    df = pd.DataFrame({"tabla": nombres})
    df["filas"] = [con.execute(f'SELECT count(*) FROM "{n}"').fetchone()[0] for n in nombres]
    df["que_es"] = df["tabla"].map(DESCRIPCION).fillna("")
    # Primero las descritas, en el orden de DESCRIPCION (la tabla central arriba)
    orden = {n: i for i, n in enumerate(DESCRIPCION)}
    df["orden"] = df["tabla"].map(orden).fillna(len(orden))
    return df.sort_values(["orden", "tabla"]).drop(columns="orden").reset_index(drop=True)


@st.cache_data(ttl=TTL, max_entries=4)
def leer(tabla: str) -> pd.DataFrame:
    return conexion().cursor().execute(f'SELECT * FROM "{tabla}"').df()


def _csv(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8-sig")


@st.cache_data(ttl=TTL, max_entries=4)
def excel(tabla: str) -> bytes:
    salida = io.BytesIO()
    leer(tabla).to_excel(salida, index=False, sheet_name=tabla[:31])
    return salida.getvalue()


@st.cache_data(ttl=TTL, max_entries=1)
def zip_principal(nombres: tuple[str, ...]) -> bytes:
    """Las tablas descritas en un solo ZIP, con un LEEME que dice que es cada una."""
    salida = io.BytesIO()
    with zipfile.ZipFile(salida, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("LEEME.txt", "\n".join(f"{n}.csv: {DESCRIPCION[n]}" for n in nombres))
        for n in nombres:
            z.writestr(f"{n}.csv", _csv(conexion().cursor().execute(f'SELECT * FROM "{n}"').df()))
    return salida.getvalue()


def mostrar() -> None:
    st.subheader("Bajá los datos para OpenRefine, Power Query o Excel")
    estilo.explicacion(
        "Son las mismas tablas que usa esta app, ya limpias y unidas. Elegí una, mirá las primeras "
        "filas y descargala. <b>CSV</b> sirve para todo (OpenRefine: <i>Create Project → This Computer</i>; "
        "Power Query: <i>Datos → Obtener datos → Desde texto/CSV</i>). <b>Excel</b> se ofrece si la tabla "
        f"tiene menos de {LIMITE_EXCEL:,} filas.".replace(",", ".")
    )
    catalogo = tablas()
    st.dataframe(catalogo, hide_index=True, width="stretch",
                 column_config={"tabla": "Tabla", "filas": st.column_config.NumberColumn("Filas", format="localized"),
                                "que_es": "Qué tiene"})

    tabla = st.selectbox("Tabla", catalogo["tabla"], key="descarga_tabla")
    df = leer(tabla)
    st.caption(f"{len(df):,} filas · {df.shape[1]} columnas · primeras 100 filas:".replace(",", "."))
    st.dataframe(df.head(100), hide_index=True, width="stretch")

    col_csv, col_xlsx = st.columns(2)
    # Los archivos se arman recien al hacer clic (callable): abrir la pestana no cuesta nada
    col_csv.download_button("⬇️ Descargar CSV", lambda: _csv(leer(tabla)), f"{tabla}.csv", "text/csv",
                            width="stretch", key="descarga_csv")
    if len(df) <= LIMITE_EXCEL:
        col_xlsx.download_button("⬇️ Descargar Excel", lambda: excel(tabla), f"{tabla}.xlsx",
                                 "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                 width="stretch", key="descarga_xlsx")
    else:
        col_xlsx.info("Muy grande para Excel: usá el CSV con Power Query.")

    st.divider()
    principales = tuple(n for n in DESCRIPCION if n in set(catalogo["tabla"]))
    st.download_button(f"⬇️ Descargar todo en un ZIP ({len(principales)} tablas en CSV + LEEME)",
                       lambda: zip_principal(principales), "caso8_datos.zip", "application/zip",
                       width="stretch", key="descarga_zip")
