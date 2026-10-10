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


def test_la_papa_criolla_es_su_propio_producto():
    """La papa criolla no va dentro de "Papa": es otra especie.

    La papa criolla es Solanum phureja y la papa comun Solanum tuberosum. El
    DANE las publica aparte, y se nota en el propio catalogo: el abastecimiento
    trae dos cajones separados, `Papa criolla` (541) y `Papas negras otras`
    (498). Juntarlas haria que la mediana de "la papa" mezcle dos especies con
    precios muy distintos (la criolla vale el doble).
    """
    por_id = {f["art_id"]: f for f in _leer_catalogo()}
    for art_id in ("159", "161", "541"):
        assert por_id[art_id]["producto"] == "Papa criolla", por_id[art_id]

    # Y al reves: ninguna papa negra debe caer en "Papa criolla".
    for fila in _leer_catalogo():
        if fila["producto"] == "Papa criolla":
            assert "criolla" in fila["articulo"].lower(), fila


def test_el_huevo_se_mide_por_unidad_y_el_aceite_por_litro():
    # Metodologia SIPSA-P: el campo de la API se llama promedioKg pero el huevo
    # va por unidad y el aceite por litro. Mezclar unidades invalida la grafica.
    for fila in _leer_catalogo():
        if fila["articulo"].startswith("Huevo"):
            assert fila["unidad"] == "unidad", fila
        if fila["articulo"].startswith("Aceite"):
            assert fila["unidad"] == "litro", fila


# --- Mejoras de la revision en vivo (C2-17 a C2-20) ---

BASE = RAIZ / "data" / "processed" / "caso8.duckdb"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def _textos(app) -> str:
    """Todo el texto visible de una pagina simulada, en un solo string."""
    partes = [e.value for e in list(app.markdown) + list(app.caption) + list(app.info)
              + list(app.warning)]
    return "\n".join(str(p) for p in partes)


@pytest.mark.skipif(not BASE.exists(), reason="falta la base DuckDB")
def test_la_canasta_familiar_usa_el_precio_semanal_y_declara_su_periodo():
    """C2-17: la canasta familiar (arroz, huevo, carnes...) sale del precio semanal.

    El periodo cubierto se lee de la base, no se escribe a mano: la ventana del
    DANE se mueve cada semana.
    """
    import duckdb

    con = duckdb.connect(str(BASE), read_only=True)
    desde, hasta = con.execute(
        "SELECT min(semana_inicio), max(semana_inicio) FROM fact_precio_semanal WHERE en_canasta"
    ).fetchone()
    con.close()

    pagina = APP / "paginas" / "canasta.py"
    app = streamlit_testing.AppTest.from_file(str(pagina), default_timeout=180).run()
    assert not app.exception, [e.message for e in app.exception]

    assert any("canasta familiar" in t.label.lower() for t in app.tabs)
    texto = _textos(app)
    for dia in (desde, hasta):
        assert f"{dia.day} {MESES[dia.month - 1]} {dia.year}" in texto


def test_el_mapa_dibuja_los_33_departamentos_y_los_sin_dato_en_gris():
    """C2-18: un departamento sin dato se dibuja gris, con leyenda "sin dato".

    Si no se dibuja, Colombia se ve recortada. No usa la base: arma la figura con
    dos departamentos inventados y el GeoJSON real.
    """
    import json

    import pandas as pd

    import graficas

    geo = json.loads((RAIZ / "config" / "geo" / "colombia_departamentos.geojson")
                     .read_text(encoding="utf-8"))
    variacion = pd.DataFrame({"dpto_codigo": ["05", "11"], "departamento": ["Antioquia", "Bogota"],
                              "mercados": [11, 4], "variacion": [3.2, -1.5]})
    fig = graficas.mapa_departamentos(variacion, geo)

    dibujados = set()
    for traza in fig.data:
        dibujados |= set(traza.locations)
    assert len(dibujados) == 33

    grises = [t for t in fig.data if t.name == "sin dato"]
    assert len(grises) == 1 and grises[0].showlegend
    assert set(grises[0].locations).isdisjoint({"05", "11"})
