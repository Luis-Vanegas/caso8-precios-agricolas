"""Punto de entrada de la app: arma el menu y abre la pagina elegida.

Correr desde la raiz del proyecto:
    .venv\\Scripts\\python.exe -m streamlit run app/streamlit_app.py

Son 7 paginas, en el orden en que se presentan: que paso, donde, por que (el
clima), que viene y como se hizo. Cada pagina vive en app/paginas/; las partes
que antes eran paginas aparte viven en app/secciones/.
"""

import sys
from pathlib import Path

import streamlit as st

# La carpeta raiz del proyecto va al path para poder importar `src.` desde
# cualquier pagina (ahi estan los indicadores y las rutas).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

st.set_page_config(page_title="Caso 8 · Precios agrícolas", page_icon="🌽", layout="wide")

menu = {
    "Lo que pasa": [
        st.Page("paginas/inicio.py", title="Inicio", icon=":material/home:", default=True),
        st.Page("paginas/canasta.py", title="Canasta", icon=":material/grid_on:"),
        st.Page("paginas/mapa.py", title="Mapa", icon=":material/map:"),
    ],
    "Por qué pasa": [
        st.Page("paginas/clima.py", title="Clima", icon=":material/rainy:"),
        st.Page("paginas/efecto_clima.py", title="¿Cuánto afecta el clima?", icon=":material/insights:"),
    ],
    "Qué viene y cómo se hizo": [
        st.Page("paginas/pronostico.py", title="Pronóstico", icon=":material/trending_up:"),
        st.Page("paginas/como_lo_hicimos.py", title="Cómo lo hicimos", icon=":material/route:"),
    ],
}

st.navigation(menu).run()
