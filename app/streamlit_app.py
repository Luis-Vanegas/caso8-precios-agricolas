"""Caso 8 — Detección temprana de volatilidad en precios agrícolas de Colombia.

Página de entrada: resumen del estado actual y contexto del proyecto.
"""

from __future__ import annotations

import streamlit as st

from datos import aviso_cache, con_indicadores, consultar, enso, frescura

st.set_page_config(page_title="Volatilidad agrícola Colombia", page_icon="🌾", layout="wide")

st.title("🌾 Volatilidad de precios agrícolas en Colombia")
st.markdown(
    "Integración de **cinco fuentes** para detectar movimientos anómalos de precios "
    "en los mercados mayoristas del país."
)

df = con_indicadores()
ultimo = int(df["periodo"].max())
mes_actual = df[df["periodo"] == ultimo]

# --- Estado actual ----------------------------------------------------------

st.subheader(f"Último periodo con dato: {ultimo // 100}-{ultimo % 100:02d}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Series vigiladas", f"{len(mes_actual):,}")
c2.metric("Alertas rojas", int((mes_actual["alerta"] == "roja").sum()))
c3.metric("Alertas amarillas", int((mes_actual["alerta"] == "amarilla").sum()))

fase = enso().sort_values(["anio", "mes"]).iloc[-1]
c4.metric("Fase ENSO", fase["fase"], f"{fase['anomalia']:+.2f} °C")

# --- Alertas del mes --------------------------------------------------------

encendidas = mes_actual[mes_actual["alerta"].isin(["roja", "amarilla"])].sort_values(
    "z_score", key=abs, ascending=False
)

st.subheader("Alertas del último mes")
if encendidas.empty:
    st.success("Ningún movimiento anómalo en el último periodo.")
else:
    st.dataframe(
        encendidas[
            ["alerta", "producto", "mercado", "precio_cop_kg", "retorno_log", "z_score", "direccion"]
        ].rename(
            columns={
                "precio_cop_kg": "precio COP/kg",
                "retorno_log": "retorno log",
                "z_score": "z-score",
            }
        ),
        width="stretch",
        hide_index=True,
    )

# --- Qué mide cada fuente ---------------------------------------------------

st.subheader("Qué aporta cada fuente")
st.markdown(
    """
| Fuente | Rol en el análisis | Frecuencia |
|---|---|---|
| **SIPSA (DANE)** | Motor de detección: precios mayoristas diarios por mercado | Diaria |
| **FAOSTAT** | Contexto estructural: producción, comercio, balances, valor | Anual |
| **NASA POWER** | Anomalía climática en zonas productoras | Mensual |
| **ONI (NOAA)** | Fase El Niño / La Niña | Mensual |
| **Pink Sheet (BM)** | Costos de insumos: fertilizantes y combustibles | Mensual |
"""
)

st.info(
    "**Por qué la alerta sale de SIPSA y no de FAOSTAT.** La detección temprana necesita "
    "frecuencia. SIPSA publica a diario. FAOSTAT publica una vez al año y con un año de "
    "rezago, así que no puede detectar nada temprano: aporta el contexto, no la señal."
)

# --- Frescura ---------------------------------------------------------------

st.subheader("Frescura de los datos")
st.dataframe(frescura(), width="stretch", hide_index=True)
aviso_cache()

st.caption(
    "Proyecto académico — Adquisición e Integración de Datos, Ingeniería en Ciencia de Datos, ITM. "
    "Los umbrales de alerta son convenciones de este trabajo, no estándares oficiales."
)
