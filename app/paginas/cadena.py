"""La cadena: lluvia en la zona productora -> toneladas que llegan -> precio.

Las tres series en el mismo eje de tiempo para poder leerlas en vertical. La
pagina NO afirma que una cause la otra: solo las pone juntas.
"""

import streamlit as st

import estilo
import graficas
from datos import articulos_cadena, cadena, departamentos_cadena, fecha, tabla_existe

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

estilo.pie()
