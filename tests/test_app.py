"""Prueba de humo de la app: cada pagina abre sin errores.

Usa AppTest, el simulador de Streamlit: corre la pagina sin navegador y
guarda las excepciones. Necesita la base data/processed/caso8.duckdb; si no
existe (por ejemplo en un clon nuevo), la prueba se salta en vez de fallar.
"""

import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
APP = RAIZ / "app"
PAGINAS = sorted((APP / "paginas").glob("*.py"))

streamlit_testing = pytest.importorskip("streamlit.testing.v1")


@pytest.fixture(autouse=True)
def _rutas(monkeypatch):
    # Igual que streamlit_app.py: la raiz (para `src`) y app/ (para `estilo`, `datos`).
    monkeypatch.syspath_prepend(str(RAIZ))
    monkeypatch.syspath_prepend(str(APP))


@pytest.mark.skipif(not (RAIZ / "data" / "processed" / "caso8.duckdb").exists(),
                    reason="falta la base DuckDB")
@pytest.mark.parametrize("pagina", PAGINAS, ids=lambda p: p.stem)
def test_la_pagina_abre_sin_errores(pagina):
    app = streamlit_testing.AppTest.from_file(str(pagina), default_timeout=60).run()
    assert not app.exception, [e.message for e in app.exception]


def test_cada_pagina_esta_en_el_menu():
    texto = (APP / "streamlit_app.py").read_text(encoding="utf-8")
    assert texto.count("st.Page(") == len(PAGINAS)
    for pagina in PAGINAS:
        assert f"paginas/{pagina.name}" in texto, f"{pagina.name} no esta en el menu"
