"""Clima: El Nino / La Nina y la lluvia en las zonas productoras."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import estilo
import graficas
from datos import clima, consultar, enso, tabla_existe

estilo.aplicar()
estilo.encabezado(
    "Clima y El Niño",
    "El clima mueve la oferta de alimentos: una sequía o un aguacero en la zona productora "
    "se nota en el precio semanas o meses después.",
    antetitulo="Contexto",
)

e = enso()
actual = e.iloc[-1]
estilo.contadores([
    (f"ONI {actual['trimestre']} {int(actual['anio'])}", round(float(actual["anomalia"]), 2), "°C", estilo.ROJO),
    ("umbral de El Niño", 0.5, "°C", estilo.GRIS),
])
estilo.explicacion(
    "El <b>ONI</b> mide cuánto más caliente (o frío) está el océano Pacífico frente a lo normal. "
    "Por encima de <b>+0,5 °C</b> hay <b>El Niño</b>: en Colombia suele traer menos lluvia. "
    "Por debajo de <b>−0,5 °C</b> hay <b>La Niña</b>: más lluvia. Un estudio del Banco de la "
    "República encontró que un El Niño fuerte sube la inflación de alimentos a los 4 y 5 meses."
)
desde = st.slider("Desde el año", int(e["anio"].min()), int(e["anio"].max()) - 1, 2000)
estilo.grafica(graficas.oni(e, desde))

# --- Sensor IDEAM -------------------------------------------------------------------
st.subheader("Lluvia medida por sensores del IDEAM")
if tabla_existe("fact_sensor_ideam"):
    s = consultar("SELECT * FROM fact_sensor_ideam WHERE variable = 'precipitacion' ORDER BY anio, mes")
    depto = st.selectbox("Departamento", sorted(s["departamento"].unique()))
    d = s[s["departamento"] == depto].copy()
    d["fecha"] = pd.to_datetime(dict(year=d["anio"], month=d["mes"], day=1))
    fig = go.Figure(go.Bar(x=d["fecha"], y=d["anomalia"],
                           marker_color=[estilo.AZUL if v > 0 else estilo.TIERRA for v in d["anomalia"]],
                           customdata=d[["valor", "n_estaciones"]],
                           hovertemplate="%{x|%b %Y}: %{customdata[0]:.0f} mm en el mes "
                                         "(%{customdata[1]} estaciones)<br>vs normal: %{y:+.0f} mm<extra></extra>"))
    fig.update_layout(title=f"Lluvia del mes frente a lo normal · {depto} (mm)", height=340)
    estilo.grafica(fig)
    st.caption("Mediana de las estaciones válidas del departamento. Azul = llovió más que lo normal; café = menos.")
else:
    st.info(
        "Todavía no se ha cargado. Correr en orden: `scripts/probe_ideam.py`, "
        "`scripts/actualizar.py --solo ideam`, `scripts/preparar.py` y `scripts/integrar.py`."
    )

# --- NASA POWER -----------------------------------------------------------------------
st.subheader("Lluvia en las zonas productoras (NASA POWER)")
c = clima()
c1, c2 = st.columns(2)
producto = c1.selectbox("Cultivo", sorted(c["producto"].unique()))
departamento = c2.selectbox("Zona", sorted(c.loc[c["producto"] == producto, "departamento"].unique()))
z = c[(c["producto"] == producto) & (c["departamento"] == departamento)].copy()
z = z[z["anio"] >= 2015]
z["fecha"] = pd.to_datetime(dict(year=z["anio"], month=z["mes"], day=1))
fig = go.Figure(go.Bar(x=z["fecha"], y=z["precipitacion_anomalia"],
                       marker_color=[estilo.AZUL if v > 0 else estilo.TIERRA for v in z["precipitacion_anomalia"]],
                       hovertemplate="%{x|%b %Y}: %{y:+.2f} mm/día vs normal<extra></extra>"))
fig.update_layout(title=f"Lluvia frente a lo normal · {producto} en {departamento} (mm/día)", height=340)
estilo.grafica(fig)
estilo.explicacion(
    "NASA POWER promedia una cuadrícula de unos 50 km: mezcla valle y montaña. Por eso no "
    "miramos la lluvia absoluta sino la <b>anomalía</b>: cuánto llovió más o menos que el "
    "promedio de ese mismo mes en esa misma cuadrícula. Así el error de altura se cancela.",
    etiqueta="Limitación",
)
estilo.pie()
