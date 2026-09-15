"""Serie de precio, volatilidad y alertas de un producto en un mercado."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from datos import con_indicadores, puente

st.set_page_config(page_title="Detalle por producto", page_icon="📈", layout="wide")
st.title("📈 Detalle por producto")

df = con_indicadores()

c1, c2 = st.columns(2)
producto = c1.selectbox("Producto", sorted(df["producto"].unique()))
mercados = sorted(df[df["producto"] == producto]["mercado"].unique())
mercado = c2.selectbox("Mercado", mercados)

serie = df[(df["producto"] == producto) & (df["mercado"] == mercado)].sort_values("periodo")
serie["fecha"] = pd.to_datetime(
    serie["anio"].astype(str) + "-" + serie["mes"].astype(str) + "-01"
)

if serie.empty:
    st.warning("Sin datos para esa combinación.")
    st.stop()

# --- Resumen ----------------------------------------------------------------

ultimo = serie.iloc[-1]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Último precio", f"${ultimo['precio_cop_kg']:,.0f} /kg")
c2.metric(
    "Volatilidad anualizada",
    f"{ultimo['volatilidad_anualizada']:.0%}" if pd.notna(ultimo["volatilidad_anualizada"]) else "sin dato",
)
c3.metric("Meses con dato", f"{len(serie)}")
c4.metric("Alertas encendidas", int(serie["alerta"].isin(["roja", "amarilla"]).sum()))

# --- Gráficos ---------------------------------------------------------------

st.subheader("Precio mensual")
st.line_chart(serie.set_index("fecha")[["precio_cop_kg", "precio_min", "precio_max"]])

st.subheader("Volatilidad móvil de 12 meses, anualizada")
st.line_chart(serie.set_index("fecha")[["volatilidad_anualizada"]])

st.subheader("Retorno logarítmico mes a mes")
st.bar_chart(serie.set_index("fecha")[["retorno_log"]])

# --- Homologación -----------------------------------------------------------

fila = puente()[puente()["producto_sipsa"] == producto]
if not fila.empty:
    f = fila.iloc[0]
    st.subheader("Correspondencia con FAOSTAT")
    if f["permite_comparar_precio"]:
        st.success(
            f"Correspondencia **exacta** con el ítem {f['item_codigo_fao']} "
            f"({f['item_fao']}). El precio productor de FAO sí es comparable con este producto."
        )
    elif pd.isna(f["item_codigo_fao"]):
        st.error(
            "FAOSTAT **no publica** este producto para Colombia. "
            "El análisis se sostiene solo con datos de SIPSA."
        )
    else:
        st.warning(
            f"Correspondencia **{f['tipo_correspondencia']}** con el ítem "
            f"{f['item_codigo_fao']} ({f['item_fao']}). FAO agrupa varios productos en ese ítem, "
            "así que su precio productor **no** corresponde a este producto por separado. "
            "Comparar los dos precios produciría un margen inventado."
        )

# --- Tabla ------------------------------------------------------------------

with st.expander("Ver la serie completa"):
    st.dataframe(
        serie[
            ["periodo", "precio_cop_kg", "precio_min", "precio_max", "dias_con_dato",
             "retorno_log", "volatilidad_anualizada", "z_score", "alerta"]
        ],
        width="stretch",
        hide_index=True,
    )
