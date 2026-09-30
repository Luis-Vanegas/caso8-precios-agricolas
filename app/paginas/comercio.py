"""Produccion y comercio (FAOSTAT): cuanto de lo que consumimos viene de afuera."""

import streamlit as st

import estilo
import graficas
from datos import consultar
from src.indicators.volatilidad import dependencia_importaciones

estilo.aplicar()
estilo.encabezado(
    "Producción y comercio",
    "Datos anuales de la FAO. No sirven para alertar a tiempo (llegan con un año de retraso), "
    "pero explican por qué algunos precios dependen del dólar y del mercado internacional.",
    antetitulo="Contexto",
)
estilo.explicacion(
    "La <b>dependencia de importaciones</b> dice qué parte de lo que consume el país viene de "
    "afuera: importaciones ÷ (producción + importaciones − exportaciones). Si es alta, el "
    "precio interno sube cuando sube el dólar o el precio internacional."
)

comercio = consultar("SELECT * FROM fact_comercio")
produccion = consultar("SELECT * FROM fact_produccion")
items = consultar("SELECT item_codigo, item FROM dim_item_fao")
dep = dependencia_importaciones(comercio, produccion).merge(items, on="item_codigo", how="left")
# Solo productos que Colombia produce y consume en cantidad (> 1.000 t). Los agregados
# de la FAO ("Non-edible Crude Materials", "Food preparations") no tienen produccion
# y daban dependencias imposibles de mas de 100 %.
dep = dep[dep["dependencia_pct"].between(0, 100) & (dep["produccion"] > 0)
          & (dep["consumo_aparente"] > 1000)]

anio = st.selectbox("Año", sorted(dep["anio"].dropna().astype(int).unique(), reverse=True))
top = dep[dep["anio"] == anio].nlargest(15, "dependencia_pct").assign(dep=lambda d: d["dependencia_pct"] / 100)
estilo.grafica(graficas.barras_horizontales(top, "dep", "item",
                                            f"Los 15 productos más importados en {anio} (% del consumo)",
                                            color=estilo.AZUL))
st.caption("Solo productos que Colombia también produce, con consumo aparente mayor a 1.000 toneladas. Nombres tal como los publica la FAO.")

with st.expander("Ver la tabla"):
    st.dataframe(dep[dep["anio"] == anio].sort_values("dependencia_pct", ascending=False)
                 [["item", "produccion", "importacion", "exportacion", "consumo_aparente", "dependencia_pct"]],
                 width="stretch", hide_index=True)
estilo.pie()
