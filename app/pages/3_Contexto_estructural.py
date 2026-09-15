"""Contexto de FAOSTAT: producción, comercio y dependencia de importaciones."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from datos import consultar
from src.indicators.volatilidad import dependencia_importaciones

st.set_page_config(page_title="Contexto estructural", page_icon="🌍", layout="wide")
st.title("🌍 Contexto estructural")

st.markdown(
    "Datos anuales de FAOSTAT. **No sirven para detectar nada temprano**: se publican una vez "
    "al año y con rezago. Sirven para entender la exposición estructural detrás de un precio."
)

comercio = consultar("SELECT * FROM fact_comercio")
produccion = consultar("SELECT * FROM fact_produccion")
items = consultar("SELECT item_codigo, item FROM dim_item_fao")

dep = dependencia_importaciones(comercio, produccion).merge(items, on="item_codigo", how="left")
dep = dep[dep["dependencia_pct"].notna()]

# --- Dependencia por producto ----------------------------------------------

st.subheader("Dependencia de importaciones")
st.caption(
    "importación / (producción + importación − exportación) × 100, solo en toneladas. "
    "Un valor alto expone el precio interno a la tasa de cambio y al precio internacional."
)

anio = st.selectbox("Año", sorted(dep["anio"].dropna().unique(), reverse=True))
del_anio = dep[dep["anio"] == anio].sort_values("dependencia_pct", ascending=False)

st.dataframe(
    del_anio[["item", "produccion", "importacion", "exportacion",
              "consumo_aparente", "dependencia_pct"]].head(40),
    width="stretch",
    hide_index=True,
)

# --- Evolución de un ítem ---------------------------------------------------

st.subheader("Evolución de un ítem")
# Se ordena por cantidad de anios con dato para que la opcion por defecto sea
# una serie larga y no la primera alfabetica, que puede tener dos puntos.
por_historia = (
    dep.groupby("item")["anio"].nunique().sort_values(ascending=False).index.tolist()
)
item = st.selectbox(
    "Ítem FAO", por_historia, help="Ordenados por cantidad de años con dato"
)

serie = dep[dep["item"] == item].sort_values("anio")
if serie.empty:
    st.warning("Sin datos para ese ítem.")
    st.stop()

# El anio va como texto: si queda numerico, el eje lo formatea como "2,005".
serie["año"] = serie["anio"].astype(int).astype(str)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**Dependencia de importaciones (%)**")
    st.line_chart(serie.set_index("año")[["dependencia_pct"]])
with c2:
    st.markdown("**Producción, importación y exportación (t)**")
    st.line_chart(serie.set_index("año")[["produccion", "importacion", "exportacion"]])

# --- Precio productor -------------------------------------------------------

st.subheader("Precio al productor")
codigo = int(serie.iloc[0]["item_codigo"])
precio = consultar(
    f"""
    SELECT anio, mes, frecuencia, elemento, unidad, valor
    FROM fact_precio_productor
    WHERE item_codigo = {codigo} AND elemento_codigo = 5530
    ORDER BY anio, mes
    """
)
if precio.empty:
    st.info("FAOSTAT no publica precio al productor para este ítem.")
else:
    anual = precio[precio["frecuencia"] == "anual"].copy()
    anual["año"] = anual["anio"].astype(int).astype(str)
    st.caption(f"{precio.iloc[0]['elemento']} — unidad: {precio.iloc[0]['unidad']}")
    st.line_chart(anual.set_index("año")[["valor"]])
