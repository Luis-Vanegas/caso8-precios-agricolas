"""Punto de entrada de la app: arma el menu y abre la pagina elegida.

Correr desde la raiz del proyecto:
    .venv\\Scripts\\python.exe -m streamlit run app/streamlit_app.py

Cada pagina vive en app/paginas/. Este archivo solo organiza el menu en tres
secciones: lo que se ve (Panorama), como se hizo y el contexto.
"""

import sys
from pathlib import Path

import streamlit as st

# La carpeta raiz del proyecto va al path para poder importar `src.` desde
# cualquier pagina (ahi estan los indicadores y las rutas).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

st.set_page_config(page_title="Caso 8 · Precios agrícolas", page_icon="🌽", layout="wide")

menu = {
    "Panorama": [
        st.Page("paginas/inicio.py", title="Inicio", icon=":material/home:", default=True),
        st.Page("paginas/anio_actual.py", title="Lo que va de 2026", icon=":material/calendar_month:"),
        st.Page("paginas/semaforo.py", title="Semáforo de alertas", icon=":material/traffic:"),
        st.Page("paginas/canasta.py", title="Semáforo de la canasta", icon=":material/grid_on:"),
        st.Page("paginas/mapa.py", title="Mapa por departamento", icon=":material/map:"),
        st.Page("paginas/producto.py", title="Detalle por producto", icon=":material/show_chart:"),
    ],
    "Cómo lo hicimos": [
        st.Page("paginas/recorrido.py", title="Recorrido paso a paso", icon=":material/route:"),
        st.Page("paginas/sensor.py", title="Sensor IDEAM", icon=":material/water_drop:"),
        st.Page("paginas/calidad.py", title="Calidad de datos", icon=":material/fact_check:"),
    ],
    "Contexto": [
        st.Page("paginas/clima_hoy.py", title="Clima hoy", icon=":material/rainy:"),
        st.Page("paginas/clima.py", title="Clima y El Niño", icon=":material/thermostat:"),
        st.Page("paginas/comercio.py", title="Producción y comercio", icon=":material/public:"),
    ],
}

st.navigation(menu).run()
