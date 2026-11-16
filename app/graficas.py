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
# Franja de "lo normal" del termometro: mas oscura que BORDE (la franja de "lo raro")
# para que las dos se distingan sin necesitar color.
GRIS_BANDA = "#C2BEB0"


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
    fig.update_layout(title="Precio mayorista (pesos por kg)", yaxis_tickprefix="$",
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
                         hovertemplate="%{x|%b %Y}<br>a %{y:.1f} desviaciones de lo normal"
                                       "<extra></extra>"))
    tope = max(4, float(np.nanmax(np.abs(s["z_score"]))) + 0.5) if s["z_score"].notna().any() else 4
    fig.update_layout(title="¿Qué tan raro fue el cambio de cada mes?",
                      yaxis_title="desviaciones de lo normal",
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

    Espera las columnas de `resultado_pronostico_precio` (docs/contrato_datos.md):
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

    fig.update_layout(height=450, yaxis_title="precio (pesos por kg)",
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
                                        f"Precio (pesos por {unidad})"))

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
    # Encuadre fijo de Colombia (con San Andres arriba a la izquierda). Con
    # fitbounds="locations" plotly dejaba el pais chico en medio del lienzo.
    fig.update_geos(fitbounds=False, visible=False,
                    lonaxis_range=[-82, -66.5], lataxis_range=[-4.4, 13.5],
                    bgcolor="rgba(0,0,0,0)")
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


def termometro(tabla: pd.DataFrame) -> go.Figure:
    """Una fila por producto: la franja de lo normal y un punto con el cambio del mes.

    Columnas que espera `tabla` (una fila por producto, ya ordenada):
      etiqueta  texto del eje (producto y mercado)
      cambio    variacion del mes frente al anterior, en fraccion (0.35 = +35 %)
      normal_lo, normal_hi   limites de lo normal (media +- UMBRAL_AMARILLA desviaciones)
      raro_lo, raro_hi       limites de lo raro (media +- UMBRAL_ROJA desviaciones)
      alerta    'verde' | 'amarilla' | 'roja'
      detalle   texto del tooltip

    Cada fila tiene su propia franja: un producto muy volatil tiene una franja
    ancha y uno estable la tiene angosta. Un punto fuera de la franja oscura es
    una alerta; fuera de la clara, alerta roja. Es exactamente la regla del
    z-score, pero dibujada.
    """
    n = len(tabla)
    ys = list(range(n))
    fig = go.Figure()

    # Las franjas son rectangulos (shapes): cada fila tiene su ancho propio.
    for i, f in enumerate(tabla.itertuples()):
        for lo, hi, color in ((f.raro_lo, f.raro_hi, BORDE), (f.normal_lo, f.normal_hi, GRIS_BANDA)):
            fig.add_shape(type="rect", xref="x", yref="y", x0=lo, x1=hi, y0=i - 0.3, y1=i + 0.3,
                          fillcolor=color, line_width=0, layer="below")
    fig.add_vline(x=0, line_width=1, line_color=GRIS)

    # Entradas de leyenda para las franjas (los shapes no aparecen en la leyenda).
    for nombre, color in (("Franja normal", GRIS_BANDA), ("Franja rara", BORDE)):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name=nombre,
                                 marker=dict(symbol="square", size=14, color=color,
                                             line=dict(width=1, color=GRIS))))

    # Un trazo por estado: asi la leyenda dice la palabra, no solo el color.
    nombres = {"verde": "Normal", "amarilla": "Alerta amarilla", "roja": "Alerta roja"}
    for estado in ("verde", "amarilla", "roja"):
        sub = tabla[tabla["alerta"] == estado]
        fig.add_trace(go.Scatter(
            x=sub["cambio"], y=[ys[tabla.index.get_loc(i)] for i in sub.index],
            mode="markers+text", name=nombres[estado],
            text=[f"{'▲' if c > 0 else '▼'} {c * 100:+.0f} %".replace(".", ",") for c in sub["cambio"]],
            textposition="middle right", textfont=dict(size=14, color=TINTA),
            marker=dict(size=15, color=COLOR_ALERTA[estado], line=dict(width=2, color="#FFFFFF")),
            customdata=sub["detalle"], hovertemplate="%{customdata}<extra></extra>"))

    extremos = pd.concat([tabla["cambio"], tabla["normal_lo"], tabla["normal_hi"]])
    margen = 0.12
    fig.update_layout(
        height=max(320, 40 * n + 150),
        xaxis=dict(tickformat="+.0%", range=[extremos.min() - margen, extremos.max() + 2 * margen],
                   title="Cambio del precio frente al mes anterior", zeroline=False),
        yaxis=dict(tickmode="array", tickvals=ys, ticktext=tabla["etiqueta"].tolist(),
                   autorange="reversed", gridcolor="rgba(0,0,0,0)", ticks="", automargin=True),
        legend=dict(orientation="h", y=1.04, x=0, yanchor="bottom", font=dict(size=13), entrywidth=120),
        margin=dict(l=8, r=8, t=70, b=8), plot_bgcolor="#FFFFFF",
    )
    return fig


def oni_y_lluvia(enso: pd.DataFrame, lluvia: pd.DataFrame, zona: str, desde: int = 2015) -> go.Figure:
    """Dos paneles con el mismo eje de tiempo: El Nino arriba, la lluvia de la zona abajo.

    Son dos paneles y no dos ejes verticales: asi cada medida conserva su escala y
    el ojo compara las fechas. Las franjas rojas marcan los episodios de El Nino
    (cinco meses seguidos con ONI >= 0,5, la regla de NOAA) y cruzan los dos paneles.
    """
    from plotly.subplots import make_subplots

    e = _con_fecha(enso[enso["anio"] >= desde])
    ll = _con_fecha(lluvia[lluvia["anio"] >= desde])

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1,
                        subplot_titles=("El Pacífico frente a lo normal (°C)",
                                        f"Lluvia en {zona} frente a lo normal (mm por día)"))
    colores_oni = [ROJO if v >= 0.5 else AZUL if v <= -0.5 else GRIS_SIN_DATO for v in e["anomalia"]]
    fig.add_trace(go.Bar(x=e["fecha"], y=e["anomalia"], marker_color=colores_oni, showlegend=False,
                         hovertemplate="%{x|%b %Y}: %{y:+.1f} °C<extra></extra>"), row=1, col=1)
    colores_lluvia = [AZUL if v > 0 else TIERRA for v in ll["anomalia"]]
    fig.add_trace(go.Bar(x=ll["fecha"], y=ll["anomalia"], marker_color=colores_lluvia, showlegend=False,
                         hovertemplate="%{x|%b %Y}: %{y:+.1f} mm/día vs normal<extra></extra>"), row=2, col=1)

    # Episodios de El Nino: rachas de 5 o mas meses con ONI >= 0,5.
    caliente = (e["anomalia"] >= 0.5).to_numpy()
    inicio = None
    for i, activo in enumerate(list(caliente) + [False]):
        if activo and inicio is None:
            inicio = i
        elif not activo and inicio is not None:
            if i - inicio >= 5:
                fig.add_vrect(x0=e["fecha"].iloc[inicio] - pd.Timedelta(days=15),
                              x1=e["fecha"].iloc[i - 1] + pd.Timedelta(days=15),
                              fillcolor=ROJO, opacity=0.10, line_width=0, layer="below")
            inicio = None

    fig.update_layout(height=520, margin=dict(l=8, r=8, t=60, b=8), bargap=0.15)
    fig.update_xaxes(gridcolor="rgba(0,0,0,0)")
    return fig


def matriz_correlacion(tabla: pd.DataFrame, umbral_q: float) -> go.Figure:
    """Zona x rezago: la correlacion entre El Nino y la lluvia, solo donde se sostiene.

    Recibe columnas departamento, rezago_meses, coeficiente y q_valor. La celda que
    NO se sostiene (podria ser casualidad) queda en gris liso y sin numero; la que
    si se sostiene lleva color y el numero dentro. Escala divergente: cafe = llueve
    menos cuando sube El Nino, azul = llueve mas, centrada en cero.
    """
    sostiene = tabla["q_valor"] < umbral_q
    cuantas = tabla[sostiene].groupby("departamento").size().reindex(
        tabla["departamento"].unique(), fill_value=0)
    zonas = cuantas.sort_values(ascending=False, kind="stable").index.tolist()
    rezagos = sorted(tabla["rezago_meses"].unique())

    def pivote(col: str, relleno) -> pd.DataFrame:
        return tabla.pivot(index="departamento", columns="rezago_meses", values=col).reindex(
            index=zonas, columns=rezagos).fillna(relleno)

    valores = pivote("coeficiente", np.nan).where(pivote("q_valor", 1) < umbral_q)
    detalle = tabla.assign(
        txt=lambda d: np.where(
            d["q_valor"] < umbral_q, "se sostiene", "no se sostiene (puede ser casualidad)")
    ).pivot(index="departamento", columns="rezago_meses", values="txt").reindex(index=zonas, columns=rezagos)
    coef = pivote("coeficiente", np.nan)
    hover = coef.map(lambda v: f"correlación {v:+.2f}".replace(".", ",") if pd.notna(v) else "") \
        + "<br>" + detalle.fillna("")
    texto = valores.map(lambda v: f"{v:+.2f}".replace(".", ",") if pd.notna(v) else "")
    tope = max(0.3, float(np.nanmax(np.abs(valores.to_numpy(dtype=float))))) \
        if np.isfinite(valores.to_numpy(dtype=float)).any() else 0.3

    fig = go.Figure(go.Heatmap(
        z=valores.to_numpy(dtype=float), x=[f"{r}" for r in rezagos], y=zonas,
        text=texto.values, texttemplate="%{text}", textfont=dict(size=13, color=TINTA),
        customdata=hover.values, hovertemplate="<b>%{y}</b>, %{x} meses después<br>%{customdata}<extra></extra>",
        zmin=-tope, zmax=tope, hoverongaps=True, xgap=3, ygap=3,
        colorscale=[(0, TIERRA), (0.5, "#FFFFFF"), (1, AZUL)],
        colorbar=dict(title=dict(text="Correlación", side="right"), thickness=14, outlinewidth=0),
    ))
    fig.update_layout(
        height=max(300, 40 * len(zonas) + 130),
        xaxis=dict(side="top", title="Meses después de que cambia El Niño", type="category",
                   gridcolor="rgba(0,0,0,0)", ticks=""),
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)", ticks="", automargin=True),
        plot_bgcolor=GRIS_SIN_DATO, margin=dict(l=8, r=8, t=90, b=8),
    )
    return fig


def barras_se_sostienen(tabla: pd.DataFrame) -> go.Figure:
    """Una barra por eslabon: que parte de las pruebas se sostiene.

    Columnas: etiqueta, pruebas, hallazgos. La pista gris es el 100 % de las
    pruebas; la barra de color, las que se sostienen. El texto dice "N de M".
    """
    pct = tabla["hallazgos"] / tabla["pruebas"]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[1] * len(tabla), y=tabla["etiqueta"], orientation="h", marker_color=BORDE,
                         hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Bar(
        x=pct, y=tabla["etiqueta"], orientation="h", marker_color=VERDE, showlegend=False,
        text=[f"{int(h)} de {int(p)}" for h, p in zip(tabla["hallazgos"], tabla["pruebas"])],
        textposition="outside", textfont=dict(size=14, color=TINTA), cliponaxis=False,
        hovertemplate="%{y}<br>%{text} pruebas se sostienen<extra></extra>"))
    fig.update_layout(
        barmode="overlay", height=60 * len(tabla) + 70,
        xaxis=dict(range=[0, 1.18], tickformat=".0%", tickvals=[0, 0.25, 0.5, 0.75, 1],
                   title="Parte de las pruebas que se sostienen", gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(autorange="reversed", gridcolor="rgba(0,0,0,0)", ticks="", automargin=True),
        margin=dict(l=8, r=8, t=10, b=8), plot_bgcolor="#FFFFFF",
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
