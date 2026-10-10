"""Graficas de la app, hechas con Plotly.

Cada funcion recibe una tabla (DataFrame) y devuelve una figura lista para
`st.plotly_chart(fig)`. Asi las paginas no se llenan de detalles de dibujo.

Por que Plotly y no st.line_chart: Plotly deja pasar el mouse para ver cada
valor, hacer zoom, y respeta los colores del estilo.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from estilo import AMARILLO, AZUL, BORDE, COLOR_ALERTA, GRIS, ROJO, TIERRA, TINTA, VERDE
from src.indicators.volatilidad import UMBRAL_AMARILLA, UMBRAL_ROJA


# Gris claro para "sin dato" en los mapas: distinto del blanco, que es "sin cambio".
GRIS_SIN_DATO = "#DADAD4"


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
    fig.update_layout(title="Índice ONI (°C sobre lo normal)", height=360)
    return fig


def pronostico_con_banda(df: pd.DataFrame) -> go.Figure:
    """Precio real, lo que el modelo habria dicho en el pasado, y el pronostico.

    Espera las columnas de `pronostico_precio` (docs/contrato_datos.md):
    `periodo`, `tipo` ('real', 'prueba' o 'pronostico'), `valor`, `lim_inf`,
    `lim_sup`. La banda se dibuja primero para que quede detras de las lineas.

    La serie `prueba` es la mas honesta de las tres: es lo que el modelo habria
    pronosticado mes a mes en el pasado, asi que su distancia contra la linea
    real se puede medir a ojo.
    """
    def _fechas(tipo):
        parte = df[df["tipo"] == tipo]
        if parte.empty:
            return parte.assign(fecha=pd.Series(dtype="datetime64[ns]"))
        return _con_fecha(parte.assign(anio=lambda d: d["periodo"] // 100,
                                       mes=lambda d: d["periodo"] % 100))

    real, prueba, pron = _fechas("real"), _fechas("prueba"), _fechas("pronostico")
    # El precio real tiene el hueco de SIPSA (2021). Igual que en `serie_precio`,
    # se agregan los meses que faltan vacios para que la linea se corte ahi y no
    # una 2020 con 2022 con una recta. No se rellena nada.
    if not real.empty:
        real = _completar_meses(real.drop(columns="fecha"))

    fig = go.Figure()
    if not pron.empty and pron["lim_sup"].notna().any():
        fig.add_trace(go.Scatter(x=pron["fecha"], y=pron["lim_sup"], mode="lines",
                                 line=dict(width=0), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=pron["fecha"], y=pron["lim_inf"], mode="lines",
                                 line=dict(width=0), fill="tonexty",
                                 fillcolor="rgba(29,78,137,.15)", name="rango probable",
                                 hoverinfo="skip"))
    if not prueba.empty:
        fig.add_trace(go.Scatter(x=prueba["fecha"], y=prueba["valor"], mode="lines",
                                 name="lo que el modelo habría dicho",
                                 line=dict(color=GRIS, width=1.4, dash="dot"),
                                 connectgaps=False,
                                 hovertemplate="%{x|%b %Y}: $%{y:,.0f} (prueba)<extra></extra>"))
    fig.add_trace(go.Scatter(x=real["fecha"], y=real["valor"], mode="lines", name="precio real",
                             line=dict(color=TINTA, width=2), connectgaps=False,
                             hovertemplate="%{x|%b %Y}: $%{y:,.0f}<extra></extra>"))
    if not pron.empty:
        fig.add_trace(go.Scatter(x=pron["fecha"], y=pron["valor"], mode="lines+markers",
                                 name="pronóstico", line=dict(color=AZUL, width=2.2, dash="dot"),
                                 marker=dict(size=6),
                                 hovertemplate="%{x|%b %Y}: $%{y:,.0f} (pronóstico)<extra></extra>"))
        if not real.empty:
            fig.add_vline(x=real["fecha"].max(), line_dash="dot", line_color=GRIS, line_width=1.2)

    fig.update_layout(height=450, yaxis_title="precio (COP por kg)",
                      legend=dict(orientation="h", y=-0.22))
    return fig


def cadena_lluvia_oferta_precio(cadena: pd.DataFrame, unidad: str = "kg") -> go.Figure:
    """Tres paneles apilados con el mismo eje X: lluvia, toneladas y precio.

    Comparten el eje de tiempo para poder leer en vertical: si un mes llovio
    mucho, ver que paso con las toneladas y con el precio en ese mismo mes y en
    los siguientes. Cada serie corta donde no tiene dato.
    """
    from plotly.subplots import make_subplots

    c = _con_fecha(cadena.assign(anio=cadena["periodo"] // 100, mes=cadena["periodo"] % 100))
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=.06,
                        subplot_titles=("Lluvia en la zona productora (mm al mes)",
                                        "Toneladas que entraron a la central",
                                        f"Precio (COP por {unidad})"))

    fig.add_trace(go.Bar(x=c["fecha"], y=c["lluvia_mm"], marker_color=AZUL, opacity=.85,
                         name="lluvia",
                         hovertemplate="%{x|%b %Y}: %{y:.0f} mm<extra></extra>"), row=1, col=1)
    fig.add_trace(go.Scatter(x=c["fecha"], y=c["toneladas"], mode="lines+markers", name="toneladas",
                             line=dict(color=TIERRA, width=2), marker=dict(size=4),
                             connectgaps=False,
                             hovertemplate="%{x|%b %Y}: %{y:,.0f} t<extra></extra>"), row=2, col=1)
    fig.add_trace(go.Scatter(x=c["fecha"], y=c["precio"], mode="lines+markers", name="precio",
                             line=dict(color=TINTA, width=2), marker=dict(size=5),
                             connectgaps=False,
                             hovertemplate="%{x|%b %Y}: $%{y:,.0f}<extra></extra>"), row=3, col=1)

    fig.update_layout(height=700, showlegend=False, bargap=.15)
    fig.update_yaxes(rangemode="tozero")
    return fig


def clima_dia_a_dia(clima: pd.DataFrame) -> go.Figure:
    """Lluvia (barras, eje izquierdo) y temperatura (lineas, eje derecho).

    Lo observado va solido y el pronostico punteado, con el mismo color: es la
    misma variable medida de dos maneras, no dos variables distintas.
    """
    fig = go.Figure()
    obs = clima[clima["tipo"] == "observado"]
    pro = clima[clima["tipo"] == "pronostico"]

    fig.add_trace(go.Bar(x=obs["fecha"], y=obs["precipitacion_mm"], name="lluvia observada",
                         marker_color=AZUL, opacity=.85,
                         hovertemplate="%{x|%d %b}: %{y:.1f} mm<extra></extra>"))
    if not pro.empty:
        # El pronostico va en el mismo azul pero translucido y con borde: una
        # barra de contorno se lee como "estimado" sin cambiar de color.
        fig.add_trace(go.Bar(x=pro["fecha"], y=pro["precipitacion_mm"], name="lluvia pronosticada",
                             marker_color="rgba(29,78,137,.30)",
                             marker_line=dict(color=AZUL, width=1),
                             hovertemplate="%{x|%d %b}: %{y:.1f} mm (pronóstico)<extra></extra>"))

    for df, guion, etiqueta in ((obs, "solid", "observada"), (pro, "dot", "pronosticada")):
        if df.empty:
            continue
        fig.add_trace(go.Scatter(x=df["fecha"], y=df["temp_max"], yaxis="y2", mode="lines",
                                 name=f"temp. máxima {etiqueta}",
                                 line=dict(color=TIERRA, width=1.8, dash=guion),
                                 hovertemplate="%{x|%d %b}: %{y:.1f} °C<extra></extra>"))
        fig.add_trace(go.Scatter(x=df["fecha"], y=df["temp_min"], yaxis="y2", mode="lines",
                                 name=f"temp. mínima {etiqueta}",
                                 line=dict(color=TIERRA, width=1.1, dash=guion), opacity=.6,
                                 hovertemplate="%{x|%d %b}: %{y:.1f} °C<extra></extra>"))

    # Linea que separa lo medido de lo pronosticado.
    if not pro.empty and not obs.empty:
        fig.add_vline(x=pro["fecha"].min(), line_dash="dot", line_color=GRIS, line_width=1.2)

    fig.update_layout(
        height=420, barmode="overlay",
        yaxis=dict(title="lluvia (mm)"),
        yaxis2=dict(title="temperatura (°C)", overlaying="y", side="right",
                    gridcolor="rgba(0,0,0,0)"),
        legend=dict(orientation="h", y=-0.18),
    )
    return fig


def lluvia_esperada(estacional: pd.DataFrame) -> go.Figure:
    """Lluvia esperada por mes: banda p10-p90 y la mediana p50.

    La banda dice que tan de acuerdo estan los miembros del ensamble: ancha es
    poca certeza. Se dibuja la banda y no solo la linea para que eso se vea.
    """
    e = _con_fecha(estacional)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=e["fecha"], y=e["precip_p90"], mode="lines", name="p90",
                             line=dict(width=0), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(x=e["fecha"], y=e["precip_p10"], mode="lines", name="rango probable",
                             line=dict(width=0), fill="tonexty",
                             fillcolor="rgba(29,78,137,.15)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=e["fecha"], y=e["precip_p50"], mode="lines+markers",
                             name="lluvia esperada (mediana)",
                             line=dict(color=AZUL, width=2.2, dash="dot"),
                             hovertemplate="%{x|%b %Y}: %{y:.0f} mm<extra></extra>"))
    fig.update_layout(height=360, yaxis_title="lluvia del mes (mm)",
                      legend=dict(orientation="h", y=-0.2))
    return fig


def mapa_departamentos(variacion: pd.DataFrame, geojson: dict) -> go.Figure:
    """Departamentos coloreados por variacion % del precio, contra el mes anterior.

    La escala es divergente y **simetrica alrededor de cero**: si no lo fuera, un
    mismo color significaria "subio" en un mes y "bajo" en otro. Azul = bajo,
    rojo = subio, blanco = sin cambio.

    Se dibujan siempre los 33 departamentos, para que Colombia se vea completa.
    Los que no tienen dato van en gris claro, con su propia entrada "sin dato"
    en la leyenda. Nunca se pintan de un color de la escala: el blanco ya
    significa "sin cambio" y el gris significa "no sabemos".
    """
    fig = go.Figure()

    # Capa de abajo: los departamentos sin dato, en gris. Va primero para que
    # quede debajo de la capa con colores.
    sin_dato = [f for f in geojson["features"]
                if f["properties"]["DPTO"] not in set(variacion["dpto_codigo"])]
    fig.add_trace(go.Choropleth(
        geojson=geojson, featureidkey="properties.DPTO",
        locations=[f["properties"]["DPTO"] for f in sin_dato],
        z=[0] * len(sin_dato),   # un solo valor: el color sale de la escala de un tono
        text=[f["properties"]["NOMBRE_DPT"].title() for f in sin_dato],
        hovertemplate="<b>%{text}</b><br>sin dato de este artículo<extra></extra>",
        colorscale=[(0, GRIS_SIN_DATO), (1, GRIS_SIN_DATO)], showscale=False,
        marker_line_color=BORDE, marker_line_width=0.6,
        name="sin dato", showlegend=True,
    ))

    # El limite lo fija el departamento que mas se movio, con un piso de 5 % para
    # que un mes tranquilo no se vea como una crisis de colores.
    tope = max(5.0, float(variacion["variacion"].abs().max() or 0))
    fig.add_trace(go.Choropleth(
        geojson=geojson, locations=variacion["dpto_codigo"], featureidkey="properties.DPTO",
        z=variacion["variacion"],
        customdata=np.stack([variacion["departamento"], variacion["mercados"]], axis=-1),
        hovertemplate=("<b>%{customdata[0]}</b><br>%{z:+.1f}% frente al mes anterior"
                       "<br>mediana de %{customdata[1]} mercado(s)<extra></extra>"),
        zmin=-tope, zmax=tope,
        colorscale=[(0, AZUL), (0.5, "#FFFFFF"), (1, ROJO)],
        marker_line_color=BORDE, marker_line_width=0.6,
        colorbar=dict(title=dict(text="% frente al<br>mes anterior", side="right"),
                      ticksuffix="%", thickness=14, len=0.8, outlinewidth=0),
        name="con dato", showlegend=False,
    ))
    fig.update_geos(fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)")
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0), dragmode=False,
                      legend=dict(y=0.02, x=0.02, bgcolor="rgba(255,255,255,.85)",
                                  bordercolor=BORDE, borderwidth=1))
    return fig


def matriz_semaforo(matriz: pd.DataFrame, glifos: pd.DataFrame, detalle: pd.DataFrame,
                    etiquetas: list[str]) -> go.Figure:
    """Matriz producto x periodo: una celda por mes, pintada con su estado.

    Recibe las tres tablas ya armadas por `datos.matriz_canasta` (severidad,
    glifo y texto del tooltip) para no mezclar calculo con dibujo.

    La escala es categorica, no continua: 0 verde, 1 amarilla, 2 roja. Plotly
    necesita los cortes en fracciones del rango, de ahi los tercios.
    """
    fig = go.Figure(go.Heatmap(
        z=matriz.values, x=etiquetas, y=matriz.index.tolist(),
        text=glifos.values, texttemplate="%{text}",
        textfont=dict(size=13, color="white"),
        customdata=detalle.values,
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{customdata}<extra></extra>",
        zmin=0, zmax=2,
        colorscale=[(0, VERDE), (1 / 3, VERDE), (1 / 3, AMARILLO), (2 / 3, AMARILLO),
                    (2 / 3, ROJO), (1, ROJO)],
        showscale=False,
        xgap=2, ygap=2,
    ))
    # Un mes sin dato queda como hueco (z vacio): se ve el fondo blanco de la
    # grafica, nunca un color que insinue "sin alerta".
    fig.update_layout(
        height=max(380, 24 * len(matriz) + 140),
        xaxis=dict(side="top", tickangle=-60, gridcolor="rgba(0,0,0,0)", ticks=""),
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)", ticks=""),
        plot_bgcolor="#FFFFFF",
        margin=dict(l=8, r=8, t=90, b=8),
    )
    return fig


def matriz_variacion(tabla: pd.DataFrame, etiquetas: list[str], detalle: pd.DataFrame) -> go.Figure:
    """Matriz fila x mes pintada por la variacion % contra el mes anterior.

    Igual que el mapa: escala divergente y simetrica alrededor de cero (azul =
    bajo, rojo = subio, blanco = casi igual). Una celda sin dato queda vacia y
    se ve el fondo, nunca un color que insinue "no cambio".
    """
    valores = tabla.to_numpy(dtype=float)
    tope = max(5.0, float(np.nanmax(np.abs(valores)))) if np.isfinite(valores).any() else 5.0
    # El numero va dentro de la celda: el color nunca va solo.
    texto = tabla.map(lambda v: f"{v:+.0f}%" if pd.notna(v) else "")
    fig = go.Figure(go.Heatmap(
        z=valores, x=etiquetas, y=tabla.index.tolist(),
        text=texto.values, texttemplate="%{text}", textfont=dict(size=11),
        customdata=detalle.values,
        hovertemplate="<b>%{y}</b><br>%{x}<br>%{customdata}<extra></extra>",
        zmin=-tope, zmax=tope,
        colorscale=[(0, AZUL), (0.5, "#FFFFFF"), (1, ROJO)],
        colorbar=dict(title=dict(text="% frente al<br>mes anterior", side="right"),
                      ticksuffix="%", thickness=14, outlinewidth=0),
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        height=max(320, 26 * len(tabla) + 140),
        xaxis=dict(side="top", tickangle=-45, gridcolor="rgba(0,0,0,0)", ticks=""),
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)", ticks=""),
        plot_bgcolor="#FFFFFF",
        margin=dict(l=8, r=8, t=80, b=8),
    )
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
