"""Graficas de la app, hechas con Plotly.

Cada funcion recibe una tabla (DataFrame) y devuelve una figura lista para
`st.plotly_chart(fig)`. Asi las paginas no se llenan de detalles de dibujo.

Por que Plotly y no st.line_chart: Plotly deja pasar el mouse para ver cada
valor, hacer zoom y animar el mapa mes a mes, y respeta los colores del estilo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from estilo import AMARILLO, AZUL, BORDE, COLOR_ALERTA, GRIS, ROJO, VERDE
from src.indicators.volatilidad import UMBRAL_AMARILLA, UMBRAL_ROJA


def _con_fecha(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega una columna `fecha` (primer dia del mes) a partir de anio y mes."""
    df = df.copy()
    df["fecha"] = pd.to_datetime(dict(year=df["anio"], month=df["mes"], day=1))
    return df


def _completar_meses(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega los meses que faltan con valores vacios.

    Sin esto, la linea une diciembre de 2020 con febrero de 2022 como si 2021
    existiera. Con los meses vacios, Plotly corta la linea y el hueco se ve.
    """
    s = _con_fecha(df).set_index("fecha")
    todos = pd.date_range(s.index.min(), s.index.max(), freq="MS")
    return s.reindex(todos).rename_axis("fecha").reset_index()


def mapa_mercados(alertas_mes: pd.DataFrame, geo: pd.DataFrame, titulo: str = "") -> go.Figure:
    """Un circulo por mercado: tamano = alertas del mes, color = la mas grave.

    alertas_mes: filas de un solo mes con columnas mercado y alerta.
    geo: coordenadas de config/mercados.csv.
    """
    gravedad = {"roja": 2, "amarilla": 1, "verde": 0}
    resumen = (
        alertas_mes.assign(g=alertas_mes["alerta"].astype(str).map(gravedad).fillna(0).astype(int))
        .groupby("mercado")
        .agg(alertas=("g", lambda s: int((s > 0).sum())), peor=("g", "max"), series=("g", "size"))
        .reset_index()
        .merge(geo, on="mercado")
    )
    nombres = {2: "con alerta roja", 1: "con alerta amarilla", 0: "sin alertas"}
    resumen["estado"] = resumen["peor"].map(nombres)
    resumen["tamano"] = 8 + resumen["alertas"] * 7

    fig = px.scatter_geo(
        resumen, lat="lat", lon="lon", size="tamano", color="estado",
        color_discrete_map={"con alerta roja": ROJO, "con alerta amarilla": AMARILLO,
                            "sin alertas": VERDE},
        category_orders={"estado": ["sin alertas", "con alerta amarilla", "con alerta roja"]},
        hover_name="mercado",
        hover_data={"alertas": True, "series": True, "tamano": False, "lat": False,
                    "lon": False, "estado": False},
        size_max=34, title=titulo,
    )
    _estilo_mapa(fig)
    return fig


def mapa_animado(con_alertas: pd.DataFrame, geo: pd.DataFrame, desde: int) -> go.Figure:
    """El mismo mapa, pero con un boton de play que recorre los meses."""
    df = con_alertas[con_alertas["periodo"] >= desde]
    df = (
        df.assign(es=df["alerta"].isin(["roja", "amarilla"]).astype(int))
        .groupby(["periodo", "mercado"])["es"].sum().reset_index(name="alertas")
        .merge(geo, on="mercado")
        .sort_values("periodo")
    )
    df["mes"] = df["periodo"].map(lambda p: f"{p // 100}-{p % 100:02d}")
    df["tamano"] = 6 + df["alertas"] * 6
    fig = px.scatter_geo(
        df, lat="lat", lon="lon", size="tamano", color="alertas", animation_frame="mes",
        hover_name="mercado", hover_data={"alertas": True, "tamano": False, "lat": False,
                                          "lon": False, "mes": False},
        color_continuous_scale=[VERDE, AMARILLO, ROJO], range_color=[0, max(3, df["alertas"].max())],
        size_max=30,
    )
    _estilo_mapa(fig)
    fig.update_layout(coloraxis_colorbar=dict(title="alertas"))
    return fig


def _estilo_mapa(fig: go.Figure) -> None:
    """Encuadre en Colombia con tierra clara y fronteras suaves."""
    fig.update_geos(
        lataxis_range=[-4.3, 12.8], lonaxis_range=[-79.6, -66.8], showframe=False,
        showland=True, landcolor="#F1ECDF", showocean=True, oceancolor="#E3ECF3",
        showcountries=True, countrycolor="#BDB6A4", showcoastlines=True, coastlinecolor="#BDB6A4",
        showlakes=False, projection_type="mercator", bgcolor="rgba(0,0,0,0)",
    )
    fig.update_layout(height=600, margin=dict(l=0, r=0, t=40, b=0), legend_title_text="",
                      legend=dict(orientation="h", y=0.02, x=0.02, bgcolor="rgba(255,255,255,.8)"))


def serie_precio(serie: pd.DataFrame) -> go.Figure:
    """Precio mensual con su rango (min-max del mes) y los meses con alerta marcados."""
    s = _completar_meses(serie)
    fig = go.Figure()
    # Banda sombreada entre el minimo y el maximo del mes. Se dibuja por tramos
    # continuos: si se dibuja de una, el relleno cruza los meses sin dato.
    tramo = s["precio_cop_kg"].isna().cumsum()
    for i, (_, t) in enumerate(s.dropna(subset=["precio_cop_kg"]).groupby(tramo)):
        fig.add_trace(go.Scatter(
            x=pd.concat([t["fecha"], t["fecha"][::-1]]),
            y=pd.concat([t["precio_max"], t["precio_min"][::-1]]),
            fill="toself", fillcolor="rgba(27,94,59,.13)", line=dict(width=0),
            name="rango del mes (mín–máx)", legendgroup="rango", showlegend=i == 0,
            hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=s["fecha"], y=s["precio_cop_kg"], name="precio promedio",
                             line=dict(color=VERDE, width=2.5),
                             hovertemplate="%{x|%b %Y}<br>$%{y:,.0f} /kg<extra></extra>"))
    for nivel in ("amarilla", "roja"):
        m = s[s["alerta"].astype(str) == nivel]
        fig.add_trace(go.Scatter(x=m["fecha"], y=m["precio_cop_kg"], mode="markers",
                                 name=f"alerta {nivel}",
                                 marker=dict(color=COLOR_ALERTA[nivel], size=12,
                                             line=dict(color="white", width=2))))
    fig.update_layout(title="Precio mayorista (COP por kg)", yaxis_tickprefix="$",
                      yaxis_tickformat=",.0f", height=400)
    return fig


def z_score(serie: pd.DataFrame) -> go.Figure:
    """Z-score de cada mes con las franjas del semaforo.

    El z-score dice cuantas desviaciones se alejo el cambio del mes de lo
    normal para esa serie. Entre -2 y 2 es normal (verde).
    """
    s = _completar_meses(serie)
    fig = go.Figure()
    for bajo, alto, color in ((UMBRAL_AMARILLA, UMBRAL_ROJA, AMARILLO), (UMBRAL_ROJA, 6, ROJO)):
        for signo in (1, -1):
            fig.add_hrect(y0=signo * bajo, y1=signo * alto, fillcolor=color, opacity=0.13,
                          line_width=0)
    colores = s["alerta"].astype(str).map(COLOR_ALERTA).fillna(GRIS)
    fig.add_trace(go.Bar(x=s["fecha"], y=s["z_score"], marker_color=colores,
                         hovertemplate="%{x|%b %Y}<br>z = %{y:.2f}<extra></extra>"))
    tope = max(4, float(np.nanmax(np.abs(s["z_score"]))) + 0.5) if s["z_score"].notna().any() else 4
    fig.update_layout(title="¿Qué tan raro fue el cambio de cada mes? (z-score)",
                      yaxis_range=[-tope, tope], height=320, showlegend=False)
    return fig


def oni(enso: pd.DataFrame, desde: int) -> go.Figure:
    """Indice ONI: rojo arriba de +0,5 (El Niño), azul abajo de -0,5 (La Niña)."""
    e = _con_fecha(enso[enso["anio"] >= desde])
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=e["fecha"], y=e["anomalia"].clip(lower=0), fill="tozeroy",
                             line=dict(color=ROJO, width=1), fillcolor="rgba(192,57,43,.35)",
                             name="más caliente (El Niño)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=e["fecha"], y=e["anomalia"].clip(upper=0), fill="tozeroy",
                             line=dict(color=AZUL, width=1), fillcolor="rgba(29,78,137,.35)",
                             name="más frío (La Niña)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=e["fecha"], y=e["anomalia"], line=dict(color="#333", width=1.2),
                             name="ONI", hovertemplate="%{x|%b %Y}: %{y:+.2f} °C<extra></extra>"))
    for y in (0.5, -0.5):
        fig.add_hline(y=y, line_dash="dot", line_color=GRIS, line_width=1)
    fig.update_layout(title="Índice ONI (°C sobre lo normal en el Pacífico)", height=360)
    return fig


def barras_horizontales(df: pd.DataFrame, x: str, y: str, titulo: str, color: str = VERDE,
                        formato: str = ".0%") -> go.Figure:
    """Ranking simple: una barra por fila, ordenado de mayor a menor."""
    d = df.sort_values(x)
    fig = go.Figure(go.Bar(x=d[x], y=d[y], orientation="h", marker_color=color,
                           hovertemplate=f"%{{y}}: %{{x:{formato}}}<extra></extra>"))
    fig.update_layout(title=titulo, height=max(320, 22 * len(d) + 80), xaxis_tickformat=formato,
                      yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    return fig


def calor_z(mes: pd.DataFrame) -> go.Figure:
    """Mapa de calor producto x mercado del z-score de un mes."""
    tabla = mes.pivot_table(index="producto", columns="mercado", values="z_score")
    tabla = tabla.loc[tabla.abs().max(axis=1).sort_values(ascending=False).index]
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=[m.title() for m in tabla.columns], y=tabla.index,
        zmin=-4, zmax=4, zmid=0,
        colorscale=[[0, AZUL], [0.5, "#FFFFFF"], [1, ROJO]],
        colorbar=dict(title="z"), hovertemplate="%{y} en %{x}<br>z = %{z:.2f}<extra></extra>",
        xgap=1, ygap=1,
    ))
    fig.update_layout(title="Cada cuadro: producto en un mercado. Rojo = subió raro, azul = bajó raro",
                      height=max(420, 20 * len(tabla) + 120), xaxis_tickangle=-40,
                      plot_bgcolor=BORDE)
    return fig
