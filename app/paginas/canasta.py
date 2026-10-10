"""Semaforo de la canasta: la historia completa de alertas, mes por mes.

La pagina "Semaforo de alertas" responde "que paso este mes". Esta responde
"que paso en todos los meses": una celda por producto y mes, para encontrar
rachas y epocas raras de un vistazo.
"""

import streamlit as st

import estilo
import graficas
from datos import fecha, matriz_canasta, ultimo_mes_cerrado

estilo.aplicar()
estilo.encabezado(
    "Semáforo de la canasta",
    "Cada celda es un producto en un mes. El color dice si ese mes su precio se movió "
    "dentro de lo normal o se salió de lo normal.",
)

estilo.explicacion(
    "Un producto se vende en varios mercados y cada mercado tiene su propia alerta. "
    "La celda muestra la <b>peor alerta del mes</b>, porque un semáforo avisa por el caso más "
    "grave, no por el promedio. Pasá el mouse por una celda para ver en cuántos mercados se "
    "encendió. Los productos con más meses en alerta quedan arriba."
)

cerrado = ultimo_mes_cerrado()
anio_final = cerrado // 100
anios = list(range(2020, anio_final + 1))
desde_anio, hasta_anio = st.select_slider(
    "Años que se muestran", options=anios, value=(max(2020, anio_final - 2), anio_final),
)

peor, glifos, detalle, etiquetas = matriz_canasta(desde_anio * 100 + 1, hasta_anio * 100 + 12)

meses_con_alerta = int((peor > 0).sum().sum())
estilo.fila_de_tarjetas([
    estilo.tarjeta("Productos", f"{len(peor)}", "los que publica SIPSA a diario"),
    estilo.tarjeta("Meses mostrados", f"{len(etiquetas)}", f"hasta {fecha(cerrado)} (último mes cerrado)"),
    estilo.tarjeta("Celdas en alerta", f"{meses_con_alerta}", "producto-mes con alerta amarilla o roja",
                   color=estilo.AMARILLO if meses_con_alerta else estilo.VERDE),
])

estilo.grafica(graficas.matriz_semaforo(peor, glifos, detalle, etiquetas))

st.caption(
    "**▲ roja** · **● amarilla** · celda verde lisa: sin alerta · celda **blanca**: ese mes no "
    "tiene dato. La franja blanca de 2021 es el hueco de SIPSA (enero de 2021 a enero de 2022): "
    "la fuente no publicó, y un hueco se muestra como hueco, nunca se rellena."
)

st.caption(
    "Leer una fila de izquierda a derecha muestra la historia de un producto; leer una columna "
    "hacia abajo muestra qué pasó en el mercado ese mes. Varias celdas encendidas en la misma "
    "columna sugieren una causa común (clima, combustible, paro), pero esta página no lo "
    "demuestra: **correlación no es causalidad**."
)

estilo.pie()
