"""La cadena: lluvia en la zona productora -> toneladas que llegan -> precio.

Las tres series en el mismo eje de tiempo para poder leerlas en vertical. La
pagina NO afirma que una cause la otra: solo las pone juntas.
"""

import streamlit as st

import estilo
import graficas
from datos import (UMBRAL_Q, articulos_cadena, cadena, departamentos_cadena, fecha,
                   sensibilidad_cadena, tabla_existe)

estilo.aplicar()
estilo.encabezado(
    "La cadena",
    "Llueve en la zona donde se siembra, llegan más o menos toneladas a la central, "
    "y el precio responde. Las tres cosas, mes por mes.",
)

if not (tabla_existe("fact_abastecimiento") and tabla_existe("fact_clima_diario")):
    st.info(
        "Esta página necesita `fact_abastecimiento`, `fact_clima_diario` y "
        "`fact_precio_semanal`. Alguna todavía no está en la base."
    )
    st.stop()

estilo.explicacion(
    "Leé la gráfica <b>en vertical</b>: buscá un mes con mucha o poca lluvia y mirá qué pasó "
    "debajo, en las toneladas y en el precio, ese mes y los siguientes. El efecto del clima "
    "tarda: entre la lluvia y la góndola pasan semanas o meses. "
    "Que dos series se muevan parecido <b>no demuestra</b> que una cause la otra: "
    "<b>correlación no es causalidad</b>. La medición formal es trabajo de los indicadores de "
    "sensibilidad al clima, no de esta página."
)

st.caption(
    "**Una aclaración necesaria:** la lluvia que se muestra es la del **mismo departamento de la "
    "central**, que no siempre es donde se cultivó lo que llegó a esa central. La papa que se "
    "vende en Bogotá puede venir de Boyacá o de Nariño. El proyecto todavía no tiene la "
    "trazabilidad origen → destino de cada carga, así que esta página compara el clima local, "
    "y eso limita lo que se puede concluir."
)

articulos = articulos_cadena()

if articulos.empty:
    st.info("Todavía no hay artículos con abastecimiento y precio a la vez.")
    st.stop()

izq, der = st.columns(2, gap="large")
with izq:
    opciones = articulos["art_id"].tolist()
    etiquetas = dict(zip(articulos["art_id"], articulos["articulo"]))
    art_id = st.selectbox("Artículo", opciones, format_func=lambda a: etiquetas[a])

zonas = departamentos_cadena(art_id)
if zonas.empty:
    st.info(f"**{etiquetas[art_id]}** no tiene abastecimiento en ningún departamento con clima "
            "descargado. Probá otro artículo.")
    st.stop()

with der:
    nombres = dict(zip(zonas["dpto_codigo"], zonas["departamento"]))
    codigo = st.selectbox("Departamento", zonas["dpto_codigo"].tolist(),
                          format_func=lambda c: nombres[c])

df = cadena(art_id, codigo)
if df.empty:
    st.info(f"No hay datos de **{etiquetas[art_id]}** en {nombres[codigo]}.")
    st.stop()

# Los meses donde las tres series existen a la vez: es el unico tramo donde la
# cadena completa se puede leer, y conviene decirlo antes de mostrarla.
completos = df.dropna(subset=["lluvia_mm", "toneladas", "precio"])
unidad = df["unidad"].dropna().iloc[0] if df["unidad"].notna().any() else "kg"

estilo.fila_de_tarjetas([
    estilo.tarjeta("Meses con lluvia", f"{int(df['lluvia_mm'].notna().sum())}", "clima observado"),
    estilo.tarjeta("Meses con toneladas", f"{int(df['toneladas'].notna().sum())}", "abastecimiento"),
    estilo.tarjeta("Meses con precio", f"{int(df['precio'].notna().sum())}", "precios semanales"),
    estilo.tarjeta("Las tres a la vez", f"{len(completos)}",
                   f"{fecha(int(completos['periodo'].min()))} a {fecha(int(completos['periodo'].max()))}"
                   if not completos.empty else "ningún mes en común",
                   color=estilo.VERDE if len(completos) >= 12 else estilo.AMARILLO),
])

if completos.empty:
    st.warning(
        "Para esta combinación no hay ningún mes con las tres series a la vez, así que la cadena "
        "no se puede leer completa. Probá otro artículo o departamento."
    )
elif len(completos) < 12:
    st.warning(
        f"**Las tres series coinciden en solo {len(completos)} meses.** "
        "Los precios semanales del DANE son una ventana móvil de doce meses y el abastecimiento "
        "va unos meses atrasado, así que el tramo comparable es corto. Alcanza para mirar, no "
        "para concluir."
    )

st.subheader(f"{etiquetas[art_id]} · {nombres[codigo]}")
estilo.grafica(graficas.cadena_lluvia_oferta_precio(df, unidad))
st.caption(
    "Arriba la lluvia del mes en la zona productora; en el medio las toneladas que entraron a la "
    "central; abajo el precio. Las líneas **se cortan donde no hay dato** y no se unen por "
    "encima del hueco: SIPSA no publicó entre enero de 2021 y enero de 2022, y ese vacío es "
    "parte del resultado."
)

# --- Lo que midieron los indicadores -----------------------------------------
st.subheader("¿Y esto se midió, o es solo mirar la gráfica?")

medido = sensibilidad_cadena(art_id, nombres[codigo])

if medido.empty:
    st.info(
        "Para esta combinación no hay ninguna medición en `indicador_sensibilidad_clima`. "
        "La gráfica de arriba sirve para explorar, no para concluir."
    )
else:
    ESLABON = {
        "oni->lluvia": "El Niño / La Niña → lluvia en la zona",
        "lluvia->oferta": "lluvia → toneladas que llegan",
        "oferta->precio": "toneladas que llegan → precio",
    }
    tabla = medido.assign(
        eslabon=medido["eslabon"].map(ESLABON).fillna(medido["eslabon"]),
        hallazgo=medido["q_valor"] < UMBRAL_Q,
    )
    hallazgos = int(tabla["hallazgo"].sum())

    st.dataframe(
        tabla[["eslabon", "rezago_meses", "coeficiente", "q_valor", "n", "hallazgo", "metodo"]],
        column_config={
            "eslabon": "Eslabón",
            "rezago_meses": st.column_config.NumberColumn("Rezago (meses)", format="%d"),
            "coeficiente": st.column_config.NumberColumn("Efecto estimado", format="%+.4f"),
            "q_valor": st.column_config.NumberColumn("q-valor", format="%.4f"),
            "n": st.column_config.NumberColumn("Meses usados", format="%d"),
            "hallazgo": st.column_config.CheckboxColumn("¿Se sostiene?"),
            "metodo": "Método",
        },
        width="stretch", hide_index=True,
        height=min(420, 36 * (len(tabla) + 1) + 3),
    )

    if hallazgos:
        st.caption(
            f"**{hallazgos} de {len(tabla)}** relaciones se sostienen estadísticamente "
            f"(q < {UMBRAL_Q:g}). El **signo** del efecto dice la dirección: negativo en "
            "«toneladas → precio» significa que cuando llega más producto, el precio baja, que es "
            "lo que uno esperaría. El **rezago** es cuántos meses después aparece el efecto."
        )
    else:
        st.caption(
            f"**Ninguna de las {len(tabla)} relaciones se sostiene** con q < {UMBRAL_Q:g}. "
            "Dicho claro: para este artículo y departamento, los datos **no alcanzan** para "
            "afirmar que el clima mueva el precio. Es un resultado válido y hay que reportarlo "
            "así, no buscar otro corte hasta que algo dé significativo."
        )

    st.caption(
        "El **q-valor** no es el p-valor: corrige por haber probado muchas parejas a la vez. "
        "Con 140 pruebas, unos cuantos p pequeños aparecen por puro azar, y el q descuenta eso. "
        "El eslabón «lluvia → precio» se calculó sobre los nombres de los precios diarios, que "
        "usan otros códigos, así que no aparece acá."
    )

estilo.pie()
