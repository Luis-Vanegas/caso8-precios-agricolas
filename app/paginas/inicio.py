"""Portada: que paso este mes, en 4 numeros y un termometro de lo normal.

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
import graficas
from datos import (con_indicadores, cobertura_canasta, enso, fecha, periodos_semanal,
                   sensibilidad_resumen, tabla_existe, ultimo_mes_cerrado, variacion_canasta)
from src.indicators.volatilidad import UMBRAL_AMARILLA, UMBRAL_ROJA

# Cuantos productos entran al termometro de la portada. El resto esta en el expander.
FILAS_TERMOMETRO = 12
# Con menos dias con dato, el promedio del mes es debil: se avisa en el tooltip.
MIN_DIAS_CONFIABLE = 5

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
if tabla_existe("col_precio_mayorista_semanal"):
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
    estilo.oni_en_palabras(oni),
    f"índice ONI de NOAA, trimestre {fase['trimestre']} {int(fase['anio'])}"
    + (", dato provisional" if bool(fase.get("provisional", False)) else ""),
    color=estilo.ROJO if oni >= 0.5 else estilo.AZUL if oni <= -0.5 else None, retraso=3))
estilo.fila_de_tarjetas(tarjetas, ancho_minimo=240)

# --- 2. El termometro: cuanto se movio cada producto frente a lo normal ----------
st.subheader(f"Qué tanto se movió cada precio en {fecha(mes)}, frente a lo normal")


def _limpio(producto: str) -> str:
    """'Papa criolla*' -> 'Papa criolla' (el asterisco marca productos con nota)."""
    return producto.replace("*", "").strip()


def _termometro_datos(mes_datos: pd.DataFrame, mercados_encendidos: pd.Series) -> pd.DataFrame:
    """Una fila por producto: la del mercado donde el cambio fue mas raro.

    Las franjas salen de la misma media y desviacion que usa la alerta, asi que
    un punto fuera de la franja oscura es exactamente una alerta amarilla.
    """
    con_z = mes_datos.dropna(subset=["z_score"]).copy()
    con_z["rareza"] = con_z["z_score"].abs()
    peor = con_z.sort_values("rareza", ascending=False).drop_duplicates("producto").copy()

    m, s = peor["media_hist"], peor["desv_hist"]
    peor["cambio"] = np.exp(peor["retorno_log"]) - 1
    peor["normal_lo"] = np.exp(m - UMBRAL_AMARILLA * s) - 1
    peor["normal_hi"] = np.exp(m + UMBRAL_AMARILLA * s) - 1
    peor["raro_lo"] = np.exp(m - UMBRAL_ROJA * s) - 1
    peor["raro_hi"] = np.exp(m + UMBRAL_ROJA * s) - 1
    peor["alerta"] = peor["alerta"].astype(str)

    def etiqueta(f) -> str:
        ciudad = f["mercado"].split(",")[0].title()
        otros = int(mercados_encendidos.get(f["producto"], 0)) - 1
        return f"{_limpio(f['producto'])} · {ciudad}" + (f" y {otros} más" if otros > 0 else "")

    def detalle(f) -> str:
        palabra = {"verde": "dentro de lo normal", "amarilla": "alerta amarilla (raro)",
                   "roja": "alerta roja (muy raro)"}[f["alerta"]]
        verbo = "subió" if f["cambio"] > 0 else "bajó"
        texto = (f"<b>{_limpio(f['producto'])}</b> en {f['mercado'].split(',')[0].title()}<br>"
                 f"El precio {verbo} {estilo.decimal(abs(f['cambio']) * 100, 0)} % en el mes<br>"
                 f"Lo normal para este producto: de {estilo.decimal(f['normal_lo'] * 100, 0, signo=True)} % "
                 f"a {estilo.decimal(f['normal_hi'] * 100, 0, signo=True)} %<br>"
                 f"Resultado: {palabra}")
        if f["dias_con_dato"] < MIN_DIAS_CONFIABLE:
            texto += f"<br><i>Ojo: solo {int(f['dias_con_dato'])} días con dato en el mes</i>"
        return texto

    peor["etiqueta"] = peor.apply(etiqueta, axis=1)
    peor["detalle"] = peor.apply(detalle, axis=1)
    return peor.sort_values("rareza", ascending=False).reset_index(drop=True)


mercados_por_producto = encendidas.groupby("producto")["mercado"].nunique()
termometro = _termometro_datos(datos_mes, mercados_por_producto)

if encendidas.empty:
    st.success("Ningún precio se movió de forma anormal este mes.")
estilo.grafica(graficas.termometro(termometro.head(FILAS_TERMOMETRO)))

estilo.explicacion(
    "<b>Cada fila</b> es un producto, en el mercado donde su precio más se movió; si hubo alerta "
    "en más mercados, dice «y 2 más».<br>"
    "<b>La franja gris oscura</b> es lo normal para ese producto: lo que suele subir o bajar de un "
    "mes a otro. <b>La clara</b> es lo raro pero posible.<br>"
    "<b>El punto</b> es el cambio de este mes. Dentro de la franja oscura, todo normal; en la "
    "clara, alerta amarilla; fuera de ella, alerta roja.<br>"
    "<b>Ojo:</b> que un precio suba no basta. Un producto muy cambiante puede subir mucho y seguir "
    "siendo normal; uno estable da alerta con un cambio mucho menor.",
    etiqueta="Cómo leer esta gráfica",
)
st.caption(
    f"Se muestran los {min(FILAS_TERMOMETRO, len(termometro))} productos cuyo precio se movió más "
    f"de lo normal, de {len(termometro)} con historia suficiente. El cambio es frente al mes anterior. "
    f"La franja usa {UMBRAL_AMARILLA:.0f} y {UMBRAL_ROJA:.0f} desviaciones estándar de la propia "
    "historia del producto. En total, "
    f"{len(encendidas)} parejas producto-mercado encendieron alerta; la historia mes a mes está "
    "en la página Canasta."
)

with st.expander(f"Ver los {len(termometro)} productos en el termómetro"):
    estilo.grafica(graficas.termometro(termometro))

# --- 3. El clima, en una linea ---------------------------------------------------
if oni >= 0.5:
    # Lo que medimos nosotros, leido de la base: no se afirma nada que la pagina de clima no muestre.
    medido = ""
    if tabla_existe("resultado_efecto_clima"):
        r = sensibilidad_resumen()
        if "oni->lluvia" in r.index and "lluvia->precio" in r.index and "oferta->precio" in r.index:
            lluvia_zonas = r.loc["oni->lluvia"]
            precio = int(r.loc["lluvia->precio", "hallazgos"] + r.loc["oferta->precio", "hallazgos"])
            pruebas_precio = int(r.loc["lluvia->precio", "pruebas"] + r.loc["oferta->precio", "pruebas"])
            medido = (
                f"<br><b>Lo que medimos nosotros:</b> El Niño sí cambia la lluvia en "
                f"{int(lluvia_zonas['departamentos_hallazgo'])} de {int(lluvia_zonas['departamentos'])} "
                f"zonas productoras, pero hacia el precio solo se sostienen {precio} de "
                f"{pruebas_precio} pruebas. Es una relación, no una causa. Las gráficas están en la "
                "página <b>¿Cuánto afecta el clima?</b>")
    estilo.explicacion(
        f"Hay <b>El Niño</b> (el Pacífico, {estilo.decimal(oni)} °C más caliente de lo normal en "
        f"{fase['trimestre']} {int(fase['anio'])}). En Colombia, un El Niño fuerte sube la "
        "inflación de alimentos a los <b>4 y 5 meses</b> (Abril-Salcedo et al., 2015)." + medido,
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
