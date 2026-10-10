"""Portada: que paso este mes, en 4 numeros y una tabla corta.

Absorbe las antiguas paginas "Lo que va de 2026" (comparacion contra el mismo
mes del ano pasado) y "Semaforo de alertas" (las alertas del mes). El mapa de
puntos ya no esta aqui: el mapa vive en su propia pagina.

Todo se calcula con el ULTIMO MES CERRADO: el mes en curso tiene pocos dias de
dato y su promedio todavia cambia.
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import estilo
from datos import (con_indicadores, cobertura_canasta, enso, fecha, periodos_semanal,
                   tabla_existe, ultimo_mes_cerrado, variacion_canasta)

estilo.aplicar()
estilo.encabezado(
    "¿Qué alimento se está disparando?",
    "Seguimos el precio mayorista de los alimentos en Colombia y avisamos cuando uno se mueve "
    "de forma anormal para ese producto en ese mercado.",
)
estilo.para_presentar(
    "Esta es la foto del último mes completo: cuatro números y los productos que más se "
    "salieron de lo normal.<br>"
    "<b>Si te preguntan «¿anormal frente a qué?»:</b> frente a la propia historia de ese "
    "producto en ese mercado; que suba no basta, tiene que subir más de lo que suele subir."
)

df = con_indicadores()
mes = ultimo_mes_cerrado()
datos_mes = df[df["periodo"] == mes]
en_curso = int(df["periodo"].max())

estilo.chips([f"Último mes cerrado: {fecha(mes)}"]
             + ([f"{fecha(en_curso)} en curso: datos parciales"] if en_curso > mes else []))

# --- 1. Los cuatro numeros -------------------------------------------------------
# Cada tarjeta dice en palabras que significa su numero, en la misma tarjeta.

# a) Productos con alguna alerta en algun mercado. Se cuentan productos, no
#    filas producto-mercado: asi un producto con alerta en 5 mercados cuenta una vez.
encendidas = datos_mes[datos_mes["alerta"].astype(str).isin(["roja", "amarilla"])]
productos_mes = datos_mes["producto"].nunique()
productos_alerta = encendidas["producto"].nunique()

# b) Productos mas caros que hace un ano. Se compara septiembre contra
#    septiembre (y no contra el mes anterior) para no confundir temporada con subida.
nacional = df.groupby(["producto", "periodo"])["precio_cop_kg"].median().unstack()
hace_un_anio = mes - 100
if hace_un_anio in nacional.columns and mes in nacional.columns:
    interanual = (nacional[mes] / nacional[hace_un_anio] - 1).dropna().sort_values()
else:
    interanual = pd.Series(dtype=float)

# c) La canasta familiar (precio semanal): cuantos articulos subieron en el
#    ultimo mes cerrado de esa fuente.
canasta = None
if tabla_existe("fact_precio_semanal"):
    meses_semanal = periodos_semanal()
    variacion = variacion_canasta()
    cerrados = [p for p in meses_semanal[~meses_semanal["parcial"]]["periodo"]
                if p in set(variacion["periodo"])]
    if cerrados:
        mes_canasta = max(cerrados)
        del_mes = variacion[variacion["periodo"] == mes_canasta]
        canasta = (int(cobertura_canasta()["articulos"]), mes_canasta,
                   int((del_mes["variacion"] > 0).sum()), len(del_mes))

# d) El Nino / La Nina: el ultimo valor del indice ONI.
fase = enso().iloc[-1]
oni = float(fase["anomalia"])
if oni >= 0.5:
    sentido_oni = (f"el Pacífico está {estilo.decimal(oni)} °C más caliente de lo normal: "
                   "hay El Niño, que en Colombia suele traer menos lluvia")
elif oni <= -0.5:
    sentido_oni = (f"el Pacífico está {estilo.decimal(-oni)} °C más frío de lo normal: "
                   "hay La Niña, que en Colombia suele traer más lluvia")
else:
    sentido_oni = "el Pacífico está cerca de lo normal: ni El Niño ni La Niña"

tarjetas = [
    estilo.cifra(
        f"{productos_alerta} de {productos_mes}",
        f"productos de plaza tuvieron un precio fuera de lo normal en {fecha(mes)}, "
        "en al menos un mercado",
        "con alerta roja o amarilla (precio diario de SIPSA)",
        color=estilo.ROJO if productos_alerta else None, retraso=0),
    estilo.cifra(
        f"{int((interanual > 0).sum())} de {len(interanual)}",
        f"productos de plaza están más caros que en {fecha(hace_un_anio)}",
        (f"el precio típico cambió {estilo.decimal(interanual.median() * 100, 0, signo=True)} % "
         "en un año (mediana)") if len(interanual) else "",
        retraso=1),
]
if canasta:
    articulos, mes_canasta, subieron, con_cambio = canasta
    tarjetas.append(estilo.cifra(
        f"{articulos} artículos",
        f"de la canasta familiar vigilamos; en {fecha(mes_canasta)} subieron {subieron} "
        f"de los {con_cambio} que se pueden comparar con el mes anterior",
        "arroz, huevo, carnes, aceite, frutas, verduras... (precio semanal)", retraso=2))
tarjetas.append(estilo.cifra(
    f"{estilo.decimal(oni, signo=True)} °C",
    sentido_oni,
    f"índice ONI de NOAA, trimestre {fase['trimestre']} {int(fase['anio'])}"
    + (", dato provisional" if bool(fase.get("provisional", False)) else ""),
    color=estilo.ROJO if oni >= 0.5 else estilo.AZUL if oni <= -0.5 else None, retraso=3))
estilo.fila_de_tarjetas(tarjetas, ancho_minimo=240)

# --- 2. Lo que mas se movio: una fila por producto ------------------------------
st.subheader(f"Lo que más se salió de lo normal en {fecha(mes)}")

if encendidas.empty:
    st.success("Ningún precio se movió de forma anormal este mes.")
else:
    tabla = encendidas.assign(
        cambio=np.exp(encendidas["retorno_log"]) - 1,      # retorno logaritmico -> % normal
        rareza=encendidas["z_score"].abs(),                # que tan lejos quedo de lo normal
    ).sort_values("rareza", ascending=False)
    # Cuantos mercados encendieron cada producto, antes de quedarnos con uno solo.
    mercados_por_producto = tabla.groupby("producto")["mercado"].nunique()
    # UNA fila por producto: la del mercado donde el cambio fue mas raro.
    tabla = tabla.drop_duplicates("producto").head(5)

    def donde(fila) -> str:
        """'POPAYÁN' -> 'Popayán y 2 mercados más'."""
        ciudad = fila["mercado"].split(",")[0].title()
        otros = int(mercados_por_producto[fila["producto"]]) - 1
        return ciudad + (f" y {otros} mercado{'s' if otros > 1 else ''} más" if otros else "")

    def que_paso(cambio: float) -> str:
        """0.35 -> '▲ subió 35 %'. Flecha y palabra: no depende solo del color."""
        flecha, verbo = ("▲", "subió") if cambio > 0 else ("▼", "bajó")
        return f"{flecha} {verbo} {estilo.decimal(abs(cambio) * 100, 0)} %"

    def que_tan_raro(alerta: str) -> str:
        return "muy raro (alerta roja)" if alerta == "roja" else "raro (alerta amarilla)"

    vista = pd.DataFrame({
        "Producto": tabla["producto"].str.replace("*", "", regex=False).str.strip(),
        "Qué pasó con el precio": tabla["cambio"].map(que_paso),
        "Dónde": tabla.apply(donde, axis=1),
        "Qué tan raro": tabla["alerta"].astype(str).map(que_tan_raro),
    })
    st.dataframe(vista, width="stretch", hide_index=True, height=36 * (len(vista) + 1) + 3)
    st.caption(
        "El cambio es frente al mes anterior. Va del cambio más raro al menos raro para ese "
        "producto. Si un producto se disparó en varios mercados, se muestra el más raro y se "
        f"cuentan los demás. En total, {len(encendidas)} parejas producto-mercado encendieron "
        "alerta; la historia mes a mes está en la página Canasta."
    )

# --- 3. El clima, en una linea ---------------------------------------------------
if oni >= 0.5:
    estilo.explicacion(
        f"Hay <b>El Niño</b> (el Pacífico, {estilo.decimal(oni)} °C más caliente de lo normal en "
        f"{fase['trimestre']} {int(fase['anio'])}). En Colombia, un El Niño fuerte sube la "
        "inflación de alimentos a los <b>4 y 5 meses</b> (Abril-Salcedo et al., 2016). Cuánto "
        "lo medimos nosotros está en la página <b>¿Cuánto afecta el clima?</b>",
        etiqueta="Ojo con el clima",
    )

# --- 4. Todos los productos frente a hace un ano (antes "Lo que va de 2026") -----
with st.expander(f"Ver todos los productos: precio de {fecha(mes)} frente a {fecha(hace_un_anio)}"):
    if interanual.empty:
        st.info("No hay precio del mismo mes del año pasado para comparar.")
    else:
        barras = interanual.copy()
        barras.index = barras.index.str.replace("*", "", regex=False)
        fig = go.Figure(go.Bar(
            x=barras.values, y=barras.index, orientation="h",
            marker_color=[estilo.ROJO if v > 0 else estilo.AZUL for v in barras.values],
            hovertemplate="%{y}: %{x:+.0%} frente a hace un año<extra></extra>"))
        fig.update_layout(title="Cambio del precio en un año (mediana de los mercados)",
                          xaxis_tickformat="+.0%", height=max(360, 22 * len(barras)),
                          yaxis=dict(gridcolor="rgba(0,0,0,0)"))
        estilo.grafica(fig)
        st.caption(
            "Cada barra es un producto. **Rojo**: hoy cuesta más que hace un año; **azul**: menos. "
            "Se compara el mismo mes para no confundir una subida con la temporada. Estar mucho "
            "más caro no siempre enciende una alerta: la alerta mira el cambio de un mes a otro."
        )

estilo.pie()
