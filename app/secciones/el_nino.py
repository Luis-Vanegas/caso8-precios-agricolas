"""El Nino / La Nina y la lluvia en las zonas productoras.

Seccion de la pagina Clima (antes era la pagina "Clima y El Nino").
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import estilo
import graficas
from datos import clima, enso


def mostrar() -> None:
    """El Nino / La Nina (ONI) y la lluvia de NASA POWER por zona productora."""
    e = enso()
    actual = e.iloc[-1]
    oni = float(actual["anomalia"])
    # Cada numero dice en la misma tarjeta que significa.
    estilo.fila_de_tarjetas([
        estilo.cifra(f"{estilo.decimal(oni, signo=True)} °C", estilo.oni_en_palabras(oni),
                     f"índice ONI, trimestre {actual['trimestre']} {int(actual['anio'])}",
                     color=estilo.ROJO if oni >= 0.5 else estilo.AZUL if oni <= -0.5 else None),
        estilo.cifra("+0,5 °C", "es el umbral: si el Pacífico pasa de ahí varios trimestres "
                     "seguidos, se declara El Niño (y en −0,5 °C, La Niña)", "regla de NOAA",
                     retraso=1),
    ], ancho_minimo=280)
    estilo.explicacion(
        "El <b>ONI</b> mide cuánto más caliente (o frío) está el océano Pacífico frente a lo normal. "
        "Por encima de <b>+0,5 °C</b> hay <b>El Niño</b>: en Colombia suele traer menos lluvia. "
        "Por debajo de <b>−0,5 °C</b> hay <b>La Niña</b>: más lluvia. Un estudio del Banco de la "
        "República encontró que un El Niño fuerte sube la inflación de alimentos a los 4 y 5 meses."
    )
    desde = st.slider("Desde el año", int(e["anio"].min()), int(e["anio"].max()) - 1, 2000)
    fig = graficas.oni(e, desde)
    fig.update_layout(title="ONI: el Pacífico vs lo normal (°C)")  # titulo corto para que no se corte
    estilo.grafica(fig)
    estilo.explicacion(
        "Cada punto es un trimestre. Lo que está <b>sobre cero</b> (rojo) es un Pacífico más caliente "
        "de lo normal; lo que está <b>bajo cero</b> (azul) es más frío. Las líneas punteadas marcan "
        "±0,5 °C: si el índice pasa de ahí durante varios trimestres seguidos, se declara El Niño o La Niña.",
        etiqueta="Cómo leerlo",
    )

    # La lluvia medida por los sensores del IDEAM va en su propia pestana de la pagina Clima.

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
    fig.update_layout(title="Lluvia vs lo normal (mm/día)", height=340)
    estilo.grafica(fig)
    st.caption(f"{producto} · zona de {departamento} · desde 2015.")
    estilo.explicacion(
        "Cada barra es un mes. <b>Azul</b>: llovió más que el promedio de ese mes en esa zona; "
        "<b>café</b>: llovió menos. La altura es la diferencia en milímetros por día.",
        etiqueta="Cómo leerlo",
    )
    estilo.explicacion(
        "NASA POWER promedia una cuadrícula de unos 50 km: mezcla valle y montaña. Por eso no "
        "miramos la lluvia absoluta sino la <b>anomalía</b>: cuánto llovió más o menos que el "
        "promedio de ese mismo mes en esa misma cuadrícula. Así el error de altura se cancela.",
        etiqueta="Limitación",
    )
