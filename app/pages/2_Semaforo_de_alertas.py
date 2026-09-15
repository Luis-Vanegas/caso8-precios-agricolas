"""Semáforo: ranking de volatilidad y alertas por producto y mercado."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from datos import con_indicadores
from src.indicators.volatilidad import UMBRAL_AMARILLA, UMBRAL_ROJA, resumen_por_producto

st.set_page_config(page_title="Semáforo de alertas", page_icon="🚦", layout="wide")
st.title("🚦 Semáforo de alertas")

st.markdown(
    f"""
Una alerta se enciende cuando el retorno del mes se aparta de la historia de esa misma serie:
**amarilla** por encima de {UMBRAL_AMARILLA} desviaciones estándar, **roja** por encima de
{UMBRAL_ROJA}. Los umbrales son convenciones de este trabajo, no estándares oficiales.
"""
)

df = con_indicadores()

periodos = sorted(df["periodo"].unique(), reverse=True)
periodo = st.selectbox(
    "Periodo", periodos, format_func=lambda p: f"{p // 100}-{p % 100:02d}"
)
mes = df[df["periodo"] == periodo]

c1, c2, c3 = st.columns(3)
c1.metric("🔴 Rojas", int((mes["alerta"] == "roja").sum()))
c2.metric("🟡 Amarillas", int((mes["alerta"] == "amarilla").sum()))
c3.metric("🟢 Verdes", int((mes["alerta"] == "verde").sum()))

st.subheader("Alertas encendidas en el periodo")
encendidas = mes[mes["alerta"].isin(["roja", "amarilla"])].sort_values(
    "z_score", key=abs, ascending=False
)
if encendidas.empty:
    st.success("Ninguna alerta en este periodo.")
else:
    st.dataframe(
        encendidas[["alerta", "producto", "mercado", "precio_cop_kg", "retorno_log",
                    "z_score", "direccion", "dias_con_dato"]],
        width="stretch",
        hide_index=True,
    )

# --- Ranking estructural ----------------------------------------------------

st.subheader("Volatilidad típica por producto")
st.caption(
    "Un producto crónicamente volátil no dispara alertas seguido: la alerta detecta lo "
    "anómalo para ese producto, no lo alto en términos absolutos. Las dos vistas se "
    "complementan y hay que leerlas juntas."
)

resumen = resumen_por_producto(df)
st.dataframe(
    resumen.rename(
        columns={
            "volatilidad_mediana": "volatilidad anualizada (mediana)",
            "precio_ultimo": "último precio COP/kg",
        }
    ),
    width="stretch",
    hide_index=True,
)

st.bar_chart(resumen.set_index("producto")["volatilidad_mediana"])
