"""Lo que va de 2026: que paso con los precios, las alertas y el clima este ano.

Ejemplo de ANALISIS con datos nuevos: todo sale de la base, asi que al correr
el pipeline con datos mas recientes, esta pagina se actualiza sola.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import estilo
from datos import con_indicadores, consultar, enso, fecha, ultimo_mes_cerrado
from src.indicators import vigilancia

estilo.aplicar()
df = con_indicadores()
cerrado = ultimo_mes_cerrado()
anio = cerrado // 100
hace_un_anio = cerrado - 100

estilo.encabezado(
    f"Lo que va de {anio}",
    f"Qué pasó con los precios, las alertas y el clima entre enero y {fecha(cerrado)}. "
    "Todo se recalcula solo cuando se cargan datos nuevos.",
)

# --- 1. Precios: comparacion contra el mismo mes del ano pasado --------------------
# Se compara agosto contra agosto (y no contra diciembre) para no confundir un
# cambio de temporada con una subida real.
nacional = df.groupby(["producto", "periodo"])["precio_cop_kg"].median().unstack()
if hace_un_anio in nacional.columns and cerrado in nacional.columns:
    interanual = (nacional[cerrado] / nacional[hace_un_anio] - 1).dropna().sort_values()
else:
    interanual = pd.Series(dtype=float)

e = enso()
oni_hoy = e.iloc[-1]
oni_dic = e[(e["anio"] == anio - 1) & (e["mes"] == 12)]["anomalia"]
alertas_anio = df[(df["anio"] == anio) & (df["periodo"] <= cerrado)]

estilo.contadores([
    (f"productos más caros que en {fecha(hace_un_anio)}", int((interanual > 0).sum()),
     f"de {len(interanual)}", estilo.ROJO),
    ("cambio típico del precio (mediana)", round(float(interanual.median() * 100), 1), "%", estilo.TINTA),
    (f"alertas en {anio} (rojas + amarillas)", int(alertas_anio["alerta"].isin(["roja", "amarilla"]).sum()),
     "", "#B38A12"),
    ("ONI hoy", round(float(oni_hoy["anomalia"]), 2), "°C", estilo.AZUL),
])

izq, der = st.columns(2, gap="large")
with izq:
    extremos = pd.concat([interanual.head(6), interanual.tail(8)])
    extremos.index = extremos.index.str.replace("*", "", regex=False)
    fig = go.Figure(go.Bar(
        x=extremos.values, y=extremos.index, orientation="h",
        marker_color=[estilo.ROJO if v > 0 else estilo.AZUL for v in extremos.values],
        hovertemplate="%{y}: %{x:+.0%}<extra></extra>"))
    fig.update_layout(title=f"Precio {fecha(cerrado)} vs {fecha(hace_un_anio)} (mediana nacional)",
                      xaxis_tickformat="+.0%", height=460, yaxis=dict(gridcolor="rgba(0,0,0,0)"))
    estilo.grafica(fig)
with der:
    por_mes = (alertas_anio.assign(alerta=alertas_anio["alerta"].astype(str))
               .groupby(["periodo", "alerta"]).size().unstack(fill_value=0))
    fig = go.Figure()
    for nivel, color in (("amarilla", estilo.AMARILLO), ("roja", estilo.ROJO)):
        if nivel in por_mes:
            fig.add_trace(go.Bar(x=[fecha(p) for p in por_mes.index], y=por_mes[nivel],
                                 name=f"alertas {nivel}s", marker_color=color))
    fig.update_layout(barmode="stack", title=f"Alertas por mes en {anio}", height=460)
    estilo.grafica(fig)

estilo.explicacion(
    "La barra de la izquierda compara cada producto contra el <b>mismo mes del año pasado</b>, "
    "porque muchos alimentos suben y bajan por temporada. Que un producto esté mucho más caro "
    "no siempre enciende una alerta: la alerta mira el cambio de <i>un mes a otro</i> frente "
    "a la historia de ese producto en ese mercado.",
    etiqueta="Cómo leerlo",
)

# --- 2. Clima: de La Nina a El Nino, y la lluvia en las zonas productoras --------------
st.subheader("El clima de este año")
c1, c2 = st.columns([1, 1.3], gap="large")
with c1:
    tramo = e[e["anio"] >= anio - 1].copy()
    tramo["fecha"] = pd.to_datetime(dict(year=tramo["anio"], month=tramo["mes"], day=1))
    fig = go.Figure(go.Scatter(
        x=tramo["fecha"], y=tramo["anomalia"], mode="lines+markers",
        line=dict(color=estilo.TINTA, width=2),
        marker=dict(size=9, color=[estilo.ROJO if v >= 0.5 else estilo.AZUL if v <= -0.5 else estilo.GRIS
                                   for v in tramo["anomalia"]]),
        hovertemplate="%{x|%b %Y}: %{y:+.2f} °C<extra></extra>"))
    for y in (0.5, -0.5):
        fig.add_hline(y=y, line_dash="dot", line_color=estilo.GRIS, line_width=1)
    fig.update_layout(title="ONI: de La Niña a El Niño", height=380, showlegend=False,
                      xaxis_tickformat="%m/%Y")
    estilo.grafica(fig)
    if not oni_dic.empty:
        antes = f"{float(oni_dic.iloc[0]):+.2f}".replace(".", ",")
        ahora = f"{float(oni_hoy['anomalia']):+.2f}".replace(".", ",")
        st.caption(f"Pasó de {antes} °C en dic. {anio - 1} a {ahora} °C en {oni_hoy['trimestre']} {anio}.")
with c2:
    lluvia = consultar(f"""
        SELECT departamento, mes, avg(precipitacion_anomalia) AS anomalia,
               bool_or(fuente = 'diario') AS parcial
        FROM fact_clima WHERE anio = {anio} GROUP BY ALL ORDER BY departamento, mes
    """)
    tabla = lluvia.pivot(index="departamento", columns="mes", values="anomalia")
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    fig = go.Figure(go.Heatmap(
        z=tabla.values, x=[meses[m - 1] for m in tabla.columns], y=tabla.index,
        zmid=0, zmin=-6, zmax=6, colorscale=[[0, estilo.TIERRA], [0.5, "#FFFFFF"], [1, estilo.AZUL]],
        colorbar=dict(title="mm/día"), xgap=2, ygap=2,
        text=np.round(tabla.values, 1), texttemplate="%{text}",
        hovertemplate="%{y}, %{x}: %{z:+.2f} mm/día vs normal<extra></extra>"))
    fig.update_layout(title="Lluvia vs lo normal por zona (mm/día)", height=380)
    estilo.grafica(fig)
    st.caption("Azul: llovió más que el promedio de ese mes; café: menos. Los meses más recientes "
               "salen del endpoint diario de NASA y pueden estar incompletos.")

# --- 3. Lista de vigilancia -------------------------------------------------------------
st.subheader(f"Lista de vigilancia para {fecha(int((pd.Period(str(cerrado), 'M') + 1).strftime('%Y%m')))}")
estilo.explicacion(
    "Esto <b>no es una predicción</b>. Buscamos productos cuyo precio se ha movido, en el pasado, "
    "junto con la lluvia de <b>1 a 3 meses antes</b> en su zona productora. Como esa lluvia ya "
    "pasó, sirve de pista para el mes que viene. Solo aparecen las parejas con una relación "
    "de al menos 0,3, y se muestra cuántas veces la pista habría acertado. Una moneda al aire "
    "acierta el 50 %.",
    etiqueta="Qué es esto",
)
clima = consultar("SELECT * FROM fact_clima")
puente = consultar("SELECT * FROM puente_zona_sipsa")
precios = consultar("SELECT * FROM fact_precio_mayorista")
ret = vigilancia.retornos_nacionales(precios)   # ya descarta el mes abierto
corr = vigilancia.correlacion_lluvia(ret, clima, puente)
proximo = int((pd.Period(str(cerrado), "M") + 1).strftime("%Y%m"))
pistas = vigilancia.senales(corr, clima, puente, proximo)
aciertos = vigilancia.acierto_historico(ret, clima, puente, corr)

if pistas.empty:
    st.info("Ninguna pareja producto-zona tiene una relación suficientemente fuerte con la lluvia.")
else:
    pistas = pistas.merge(aciertos, on=["producto", "departamento", "rezago"], how="left")
    color = {"al alza": estilo.ROJO, "a la baja": estilo.AZUL, "sin dato": estilo.GRIS}
    estilo.fila_de_tarjetas([
        estilo.tarjeta(
            f"{f.producto.replace('*', '')} · {f.departamento}",
            f"Presión {f.senal}" if f.senal != "sin dato" else "Sin dato de lluvia",
            f"Lluvia de {fecha(int(f.periodo_lluvia))}: {f.anomalia:+.2f} mm/día vs normal · "
            f"ρ = {f.spearman:+.2f} · acertó {f.tasa_acierto:.0%} de {int(f.meses)} meses",
            color=color[f.senal], retraso=i,
        )
        for i, f in enumerate(pistas.itertuples())
    ], ancho_minimo=320)
    st.caption("El porcentaje de acierto se calcula con los mismos meses con que se midió la relación, "
               "así que es optimista. La correlación no demuestra que la lluvia cause el cambio de precio.")

estilo.pie()
