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


# Paginas con controles cuyo valor por defecto no recorre todos los casos.
# Abrir la pagina no alcanza: dos errores reales de esta fase solo aparecian al
# mover un control (un rango de anios sin alertas para algun producto, y un
# departamento sin abastecimiento del articulo elegido).
PAGINAS_CON_CONTROLES = ["canasta", "mapa", "clima_hoy", "cadena", "pronostico"]

# Cuantos valores se prueban por control. El mapa tiene 284 articulos: recorrerlos
# todos haria la prueba lenta sin encontrar nada nuevo.
VALORES_POR_CONTROL = 3


@pytest.mark.skipif(not (RAIZ / "data" / "processed" / "caso8.duckdb").exists(),
                    reason="falta la base DuckDB")
@pytest.mark.parametrize("nombre", PAGINAS_CON_CONTROLES)
def test_mover_los_controles_no_rompe_la_pagina(nombre):
    """Mueve cada control de la pagina y exige que siga sin excepciones.

    Recorre los primeros valores de cada selector y los extremos del deslizador:
    el primero y el ultimo son los que descubren los casos vacios.
    """
    pagina = APP / "paginas" / f"{nombre}.py"
    app = streamlit_testing.AppTest.from_file(str(pagina), default_timeout=180).run()
    assert not app.exception, [e.message for e in app.exception]

    for indice in range(len(app.selectbox)):
        opciones = list(app.selectbox[indice].options)
        if not opciones:
            continue
        a_probar = opciones[:VALORES_POR_CONTROL] + opciones[-1:]
        for valor in dict.fromkeys(a_probar):
            app.selectbox[indice].set_value(valor).run()
            assert not app.exception, (
                f"{nombre}: el selector {indice} con el valor {valor!r} rompio la pagina: "
                f"{[e.message for e in app.exception]}"
            )

    for indice in range(len(app.select_slider)):
        opciones = list(app.select_slider[indice].options)
        if len(opciones) < 2:
            continue
        # El rango mas amplio y el mas angosto: el amplio entra en los huecos de
        # datos, el angosto deja fuera a casi todas las series.
        for rango in ((opciones[0], opciones[-1]), (opciones[0], opciones[0])):
            app.select_slider[indice].set_value(rango).run()
            assert not app.exception, (
                f"{nombre}: el deslizador con el rango {rango} rompio la pagina: "
                f"{[e.message for e in app.exception]}"
            )


# --- Catalogo de articulos (config/catalogo_articulos.csv) ---
# El catalogo decide como se agrupan los precios en la app. Si se rompe, las
# graficas promedian articulos distintos, que es justo lo que prohibe
# docs/contrato_datos.md. Estas pruebas no usan red ni base de datos.

CATALOGO = RAIZ / "config" / "catalogo_articulos.csv"
CRUDO = RAIZ / "data" / "openrefine" / "catalogo_sipsa_crudo.csv"

GRUPOS_DANE = {
    "Verduras y hortalizas", "Frutas", "Tubérculos, raíces y plátanos",
    "Granos y cereales", "Huevos y lácteos", "Carnes", "Pescados",
    "Productos procesados",
}
UNIDADES = {"kg", "unidad", "litro"}
DISTINGUE_POR = {"variedad", "calidad", "presentacion", "origen", "procesado", "unico"}


def _leer_catalogo():
    import csv
    with open(CATALOGO, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_el_catalogo_cubre_todos_los_articulos_del_crudo():
    import csv
    with open(CRUDO, encoding="utf-8-sig") as f:
        crudo = {fila["art_id"] for fila in csv.DictReader(f)}
    catalogo = {fila["art_id"] for fila in _leer_catalogo()}
    assert catalogo == crudo, f"faltan o sobran art_id: {crudo ^ catalogo}"


def test_los_art_id_no_se_repiten():
    filas = _leer_catalogo()
    assert len({f["art_id"] for f in filas}) == len(filas)


def test_los_valores_estan_en_el_vocabulario_del_contrato():
    for fila in _leer_catalogo():
        assert fila["grupo_dane"] in GRUPOS_DANE, fila
        assert fila["unidad"] in UNIDADES, fila
        assert fila["distingue_por"] in DISTINGUE_POR, fila
        assert fila["en_canasta"] in {"si", "no"}, fila


def test_no_se_agrupa_por_la_primera_palabra_del_nombre():
    # Las dos trampas que advierte docs/contrato_datos.md: "Papaya" empieza por
    # "Papa" y el tomate de arbol no es tomate.
    por_articulo = {f["articulo"]: f for f in _leer_catalogo()}
    for articulo, fila in por_articulo.items():
        if articulo.lower().startswith("papaya"):
            assert fila["producto"] == "Papaya", fila
    tomate_de_arbol = por_articulo["Tomate de árbol"]
    assert tomate_de_arbol["producto"] != "Tomate"
    assert tomate_de_arbol["grupo_dane"] == "Frutas"


def test_el_geojson_cruza_con_los_departamentos_de_la_base():
    """El mapa une por codigo DANE, nunca por nombre.

    Tres de los 33 nombres del GeoJSON no coinciden con los de la base (Bogota,
    Narino, San Andres): unir por nombre perderia esos departamentos en silencio.
    Tambien verifica que el codigo siga siendo texto con el cero a la izquierda:
    leido como numero, Antioquia pasa de '05' a '5' y el cruce falla.
    """
    import csv
    import json

    geojson = RAIZ / "config" / "geo" / "colombia_departamentos.geojson"
    geo = json.loads(geojson.read_text(encoding="utf-8"))
    codigos_geo = {f["properties"]["DPTO"] for f in geo["features"]}

    with open(RAIZ / "config" / "departamentos.csv", encoding="utf-8-sig") as f:
        codigos_dane = {fila["dpto_codigo"] for fila in csv.DictReader(f)}

    assert len(geo["features"]) == 33
    assert codigos_geo == codigos_dane, f"no cruzan: {codigos_geo ^ codigos_dane}"
    assert all(isinstance(c, str) and len(c) == 2 for c in codigos_geo)


def test_el_huevo_se_mide_por_unidad_y_el_aceite_por_litro():
    # Metodologia SIPSA-P: el campo de la API se llama promedioKg pero el huevo
    # va por unidad y el aceite por litro. Mezclar unidades invalida la grafica.
    for fila in _leer_catalogo():
        if fila["articulo"].startswith("Huevo"):
            assert fila["unidad"] == "unidad", fila
        if fila["articulo"].startswith("Aceite"):
            assert fila["unidad"] == "litro", fila
