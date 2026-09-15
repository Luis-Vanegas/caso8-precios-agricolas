"""Contexto climático: anomalía de precipitación y fase El Niño / La Niña."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from datos import clima, enso

st.set_page_config(page_title="Clima y ENSO", page_icon="🌦️", layout="wide")
st.title("🌦️ Clima y ENSO")

# --- ENSO -------------------------------------------------------------------

e = enso()
actual = e.iloc[-1]

c1, c2, c3 = st.columns(3)
c1.metric("Fase actual", actual["fase"], f"{actual['anomalia']:+.2f} °C")
c2.metric("Trimestre", f"{actual['trimestre']} {int(actual['anio'])}")
c3.metric("Estado del dato", "provisional" if actual["provisional"] else "definitivo")

st.subheader("Índice ONI")
st.caption(
    "Media móvil de tres meses de la anomalía de temperatura del mar en la región Niño 3.4. "
    "Por encima de +0,5 °C es El Niño, por debajo de −0,5 °C es La Niña. Los últimos trimestres "
    "pueden revisarse hasta dos meses después de publicados."
)

e["fecha"] = pd.to_datetime(e["anio"].astype(str) + "-" + e["mes"].astype(str) + "-01")
desde = st.slider("Desde el año", int(e["anio"].min()), int(e["anio"].max()) - 1, 1990)
st.line_chart(e[e["anio"] >= desde].set_index("fecha")[["anomalia"]])

# --- Clima por zona ---------------------------------------------------------

st.subheader("Anomalía de precipitación por zona productora")
st.warning(
    "**Limitación de la fuente.** NASA POWER entrega el promedio de una celda de grilla, no el "
    "clima del municipio. En Colombia la celda mezcla valle y montaña: a Villavicencio, que está "
    "a 467 m, le asigna 1.392 m. Por eso se usan **anomalías** y no valores absolutos: la "
    "anomalía compara cada mes contra el promedio histórico del mismo mes en la misma celda, "
    "y el sesgo de elevación se cancela."
)

c = clima()
c1, c2 = st.columns(2)
producto = c1.selectbox("Producto", sorted(c["producto"].unique()))
zonas = sorted(c[c["producto"] == producto]["departamento"].unique())
departamento = c2.selectbox("Departamento", zonas)

zona = c[(c["producto"] == producto) & (c["departamento"] == departamento)].sort_values(
    ["anio", "mes"]
)
zona["fecha"] = pd.to_datetime(zona["anio"].astype(str) + "-" + zona["mes"].astype(str) + "-01")

st.markdown("**Anomalía de precipitación (mm/día frente al promedio del mismo mes)**")
st.bar_chart(zona.set_index("fecha")[["precipitacion_anomalia"]])

with st.expander("Ver precipitación y temperatura absolutas"):
    st.caption("Recordá la limitación de arriba: estos valores son de celda, no del municipio.")
    st.line_chart(zona.set_index("fecha")[["precipitacion_mm_dia", "temperatura_c"]])
