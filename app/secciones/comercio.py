"""Produccion y comercio (FAOSTAT): cuanto de lo que consumimos viene de afuera."""

import streamlit as st

import estilo
import graficas
from datos import consultar
from src.indicators.volatilidad import dependencia_importaciones


def mostrar() -> None:
    """Dependencia de importaciones con datos anuales de FAOSTAT."""
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

    if dep.empty:
        st.warning("No hay datos de comercio para mostrar.")
        return

    anio = st.selectbox("Año", sorted(dep["anio"].dropna().astype(int).unique(), reverse=True))
    top = dep[dep["anio"] == anio].nlargest(15, "dependencia_pct").assign(dep=lambda d: d["dependencia_pct"] / 100)
    estilo.grafica(graficas.barras_horizontales(top, "dep", "item",
                                                f"Los 15 productos más importados en {anio} (% del consumo)",
                                                color=estilo.AZUL))
    st.caption(
        "Cada barra es un producto; su largo es el porcentaje del consumo del país que viene de "
        "importaciones (100 % = todo viene de afuera). Cuanto más larga, más expuesto está su precio al "
        "dólar. Solo productos que Colombia también produce, con consumo aparente mayor a 1.000 "
        "toneladas. Nombres tal como los publica la FAO."
    )

    with st.expander("Ver la tabla"):
        st.dataframe(dep[dep["anio"] == anio].sort_values("dependencia_pct", ascending=False)
                     [["item", "produccion", "importacion", "exportacion", "consumo_aparente", "dependencia_pct"]]
                     # Toneladas con punto de miles y porcentaje con coma, como en Colombia.
                     .style.format({**{c: lambda v: estilo.decimal(v, 0) for c in
                                       ["produccion", "importacion", "exportacion", "consumo_aparente"]},
                                    "dependencia_pct": lambda v: f"{estilo.decimal(v)} %"}, na_rep=""),
                     column_config={"item": "Producto (FAO)", "produccion": "Producción (t)",
                                    "importacion": "Importación (t)", "exportacion": "Exportación (t)",
                                    "consumo_aparente": "Consumo aparente (t)",
                                    "dependencia_pct": "Viene de afuera"},
                     width="stretch", hide_index=True)
