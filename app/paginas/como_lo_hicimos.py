"""Como lo hicimos: el recorrido paso a paso, la calidad de los datos y la FAO.

Absorbe las antiguas paginas "Recorrido paso a paso", "Calidad de datos" y
"Produccion y comercio". Cada una es ahora una seccion en su propia pestana.
"""

import streamlit as st

import estilo
from secciones import calidad, comercio, recorrido

estilo.aplicar()
estilo.encabezado(
    "Cómo lo hicimos",
    "De seis fuentes que no se hablan entre sí a una alerta que cualquiera entiende. "
    "Todo lo que ves aquí son datos reales del proyecto.",
    antetitulo="Integración de datos",
)
estilo.para_presentar(
    "Esta página es la del curso: cómo traemos, limpiamos, homologamos y unimos seis fuentes "
    "en una sola base, y qué problemas encontramos en ellas.<br>"
    "<b>Si te preguntan «¿qué hicieron con los datos que faltan?»:</b> nada inventado; el hueco "
    "de SIPSA (ene. 2021 a ene. 2022) se declara y se deja vacío."
)

paso_a_paso, calidad_datos, fao = st.tabs([
    "Recorrido paso a paso",
    "Calidad de datos",
    "Producción y comercio (FAO)",
])
with paso_a_paso:
    recorrido.mostrar()
with calidad_datos:
    calidad.mostrar()
with fao:
    comercio.mostrar()

estilo.pie()
