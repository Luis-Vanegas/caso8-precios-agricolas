"""Clima: lo que pasa hoy en las zonas productoras, El Nino y el sensor del IDEAM.

Absorbe las antiguas paginas "Clima hoy", "Clima y El Nino" y "Sensor IDEAM".
Cada una es ahora una seccion (app/secciones/) en su propia pestana.
"""

import streamlit as st

import estilo
from secciones import clima_hoy, el_nino, sensor

estilo.aplicar()
estilo.encabezado(
    "Clima",
    "El clima mueve la oferta de alimentos: una sequía o un aguacero en la zona donde se "
    "siembra se puede notar en el precio semanas o meses después.",
)
estilo.para_presentar(
    "Aquí está el clima de las zonas donde se siembra: lo que llovió estos días, lo que se "
    "espera y si hay El Niño.<br>"
    "<b>Si te preguntan «¿de dónde salen estos datos?»:</b> de cuatro fuentes: Open-Meteo "
    "(días y pronóstico), NOAA (El Niño), NASA POWER (historia) y los sensores del IDEAM."
)

hoy, nino, ideam = st.tabs([
    "Hoy y lo que viene",
    "El Niño y La Niña",
    "Sensor de lluvia del IDEAM",
])
with hoy:
    clima_hoy.mostrar()
with nino:
    el_nino.mostrar()
with ideam:
    sensor.mostrar()

estilo.pie()
