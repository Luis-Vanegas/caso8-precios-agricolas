"""Tests de limpieza y perfilado. Ninguno toca la red ni los datos completos.

El fixture `Prices_E_All_Data_(Normalized)_mini.zip` es un recorte real del
dominio de precios: trae filas de Colombia (anuales y mensuales) y de otros
paises, para que el filtro de area se pueda verificar de verdad. Conserva el
nombre original del archivo a proposito, porque el modulo ubica el zip por
fragmento de nombre y eso tambien queda probado.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cleaning import faostat, homologacion
from src.cleaning.sipsa import a_mensual
from src.profiling.perfil import (
    _hueco_mayor,
    comercio_imposible,
    duplicados,
    huecos_de_serie,
    negativos,
    perfilar,
)
from src.cleaning.complementarias import anomalia_precipitacion

FIXTURES = Path(__file__).parent / "fixtures"


# --- FAOSTAT ----------------------------------------------------------------

def _pp_mini() -> pd.DataFrame:
    return faostat.extraer_colombia("PP", FIXTURES)


def test_faostat_filtra_solo_colombia():
    df = _pp_mini()
    assert set(df["area_codigo"]) == {faostat.AREA_COLOMBIA}
    assert set(df["area"]) == {"Colombia"}


def test_faostat_separa_anual_de_mensual():
    """Sin esta marca, el agregado anual y los meses se suman como si fueran lo mismo."""
    df = _pp_mini()
    assert df["frecuencia"].value_counts().to_dict() == {"anual": 3, "mensual": 3}


def test_faostat_limpia_el_apostrofo_del_m49():
    df = _pp_mini()
    assert set(df["area_m49"]) == {"170"}


def test_faostat_normaliza_nombres_de_columna():
    df = _pp_mini()
    assert "Area Code" not in df.columns
    assert {"area_codigo", "item_codigo", "elemento_codigo", "valor", "anio"} <= set(df.columns)


def test_faostat_el_valor_queda_numerico():
    df = _pp_mini()
    assert pd.api.types.is_numeric_dtype(df["valor"])


# --- SIPSA mensual ----------------------------------------------------------

def _diario() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "mercado": ["BOGOTA"] * 4,
            "producto": ["Papa"] * 4,
            "producto_codigo": [1] * 4,
            "anio": [2026, 2026, 2026, 2026],
            "mes": [1, 1, 2, 2],
            "precio_cop_kg": [1000.0, 2000.0, 3000.0, 5000.0],
        }
    )


def test_sipsa_mensual_promedia_por_mes():
    m = a_mensual(_diario()).sort_values("mes")
    assert list(m["precio_cop_kg"]) == [1500.0, 4000.0]


def test_sipsa_mensual_cuenta_los_dias_con_dato():
    """Un mes con dos dias de dato no vale lo mismo que uno con veinte."""
    m = a_mensual(_diario())
    assert set(m["dias_con_dato"]) == {2}


def test_sipsa_mensual_conserva_minimo_y_maximo():
    m = a_mensual(_diario()).sort_values("mes")
    assert list(m["precio_min"]) == [1000.0, 3000.0]
    assert list(m["precio_max"]) == [2000.0, 5000.0]


# --- Perfilado --------------------------------------------------------------

def test_perfilar_cuenta_nulos_y_porcentaje():
    df = pd.DataFrame({"a": [1, None, 3, None]})
    p = perfilar(df, "t").iloc[0]
    assert p["nulos"] == 2
    assert p["pct_nulos"] == 50.0


def test_duplicados_detecta_clave_repetida():
    df = pd.DataFrame({"k": [1, 1, 2], "v": [9, 9, 9]})
    assert duplicados(df, ["k"]) == 1


def test_duplicados_ignora_claves_ausentes():
    assert duplicados(pd.DataFrame({"a": [1]}), ["no_existe"]) == 0


def test_negativos_cuenta_solo_los_menores_a_cero():
    assert negativos(pd.DataFrame({"v": [-1, 0, 5, -3]}), "v") == 2


def test_hueco_mayor_mide_el_tramo_consecutivo_mas_largo():
    assert _hueco_mayor([2000, 2005, 2006, 2007, 2010]) == 3
    assert _hueco_mayor([]) == 0
    assert _hueco_mayor([1999]) == 1


def test_huecos_de_serie_reporta_faltantes_dentro_del_rango():
    df = pd.DataFrame({"item": ["Papa"] * 3, "elemento": ["P"] * 3, "anio": [2000, 2001, 2005]})
    h = huecos_de_serie(df, ["item", "elemento"], "anio").iloc[0]
    assert h["faltantes"] == 3  # 2002, 2003, 2004
    assert h["hueco_mayor"] == 3


# --- Comercio imposible -----------------------------------------------------

def _comercio(filas) -> pd.DataFrame:
    return pd.DataFrame(filas, columns=["item", "elemento", "anio", "unidad", "valor"])


def test_comercio_ignora_items_sin_produccion_primaria():
    """Los agregados de grupo como 'Fruit' no tienen fila de produccion.

    Compararlos contra cero marcaba miles de casos falsos.
    """
    comercio = _comercio([
        ("Fruit", "Export quantity", 2020, "t", 1000.0),
        ("Papa", "Export quantity", 2020, "t", 10.0),
    ])
    produccion = _comercio([("Papa", "Production", 2020, "t", 100.0)])

    resultado = comercio_imposible(comercio, produccion)
    assert "Fruit" not in set(resultado["item"])
    assert resultado.attrs["items_no_comparables"] == 1


def test_comercio_detecta_exportacion_mayor_a_lo_disponible():
    comercio = _comercio([
        ("Papa", "Export quantity", 2020, "t", 150.0),
        ("Papa", "Import quantity", 2020, "t", 20.0),
    ])
    produccion = _comercio([("Papa", "Production", 2020, "t", 100.0)])

    resultado = comercio_imposible(comercio, produccion)
    assert len(resultado) == 1
    assert resultado.iloc[0]["disponible"] == 120.0


def test_comercio_no_mezcla_toneladas_con_cabezas_de_animal():
    """Sumar 't' con 'An' daria un total sin significado fisico."""
    comercio = _comercio([
        ("Ganado", "Export quantity", 2020, "An", 5000.0),
        ("Ganado", "Export quantity", 2020, "t", 10.0),
    ])
    produccion = _comercio([("Ganado", "Production", 2020, "t", 100.0)])

    resultado = comercio_imposible(comercio, produccion)
    assert resultado.empty  # 10 t exportadas contra 100 t producidas


# --- Anomalia de precipitacion ----------------------------------------------

def test_anomalia_compara_cada_mes_contra_su_propio_mes():
    """En un pais bimodal, comparar contra el promedio anual no dice nada."""
    df = pd.DataFrame(
        {
            "producto": ["Papa"] * 4,
            "departamento": ["Boyaca"] * 4,
            "mes": [1, 1, 7, 7],
            "PRECTOTCORR": [2.0, 4.0, 10.0, 20.0],
        }
    )
    r = anomalia_precipitacion(df)
    # Enero promedia 3 y julio 15: cada mes contra su propia base.
    assert list(r["PRECTOTCORR_anomalia"]) == [-1.0, 1.0, -5.0, 5.0]


# --- Homologacion SIPSA - FAOSTAT -------------------------------------------

def test_homologacion_cubre_los_33_productos_de_sipsa():
    """El mapeo real tiene que seguir el paso de la fuente."""
    mapeo = homologacion.cargar()
    assert len(mapeo) == 33
    assert mapeo["producto_sipsa"].is_unique


def test_homologacion_solo_usa_tipos_conocidos():
    mapeo = homologacion.cargar()
    assert set(mapeo["tipo_correspondencia"]) <= homologacion.TIPOS_VALIDOS


def test_homologacion_sin_equivalente_no_lleva_codigo():
    mapeo = homologacion.cargar()
    sin = mapeo[mapeo["tipo_correspondencia"] == "sin_equivalente"]
    assert sin["item_codigo_fao"].isna().all()


def _mapeo(filas) -> pd.DataFrame:
    df = pd.DataFrame(
        filas, columns=["producto_sipsa", "item_codigo_fao", "item_fao", "tipo_correspondencia"]
    )
    df["item_codigo_fao"] = df["item_codigo_fao"].astype("Int64")
    return df


def test_validar_detecta_producto_sin_homologar():
    problemas = homologacion.validar(
        _mapeo([("Papa negra*", 116, "Potatoes", "agregada")]),
        {"Papa negra*", "Lulo"},
        {116},
    )
    assert any("sin homologar" in p and "Lulo" in p for p in problemas)


def test_validar_detecta_producto_que_la_fuente_dejo_de_publicar():
    problemas = homologacion.validar(
        _mapeo([("Papa negra*", 116, "Potatoes", "agregada"), ("Fantasma", 116, "Potatoes", "exacta")]),
        {"Papa negra*"},
        {116},
    )
    assert any("ya no publica" in p for p in problemas)


def test_validar_detecta_codigo_fao_inexistente():
    problemas = homologacion.validar(
        _mapeo([("Papa negra*", 999, "Inventado", "exacta")]),
        {"Papa negra*"},
        {116},
    )
    assert any("no existen para Colombia" in p for p in problemas)


def test_validar_acepta_un_mapeo_consistente():
    assert homologacion.validar(
        _mapeo([("Papa negra*", 116, "Potatoes", "agregada")]),
        {"Papa negra*"},
        {116},
    ) == []


def test_colisiones_marca_los_items_que_reciben_varios_productos():
    """Guayaba y mango caen en el mismo item: ese precio no es de ninguno de los dos."""
    choques = homologacion.colisiones(
        _mapeo([
            ("Guayaba*", 571, "Mangoes, guavas and mangosteens", "agregada"),
            ("Mango tommy", 571, "Mangoes, guavas and mangosteens", "agregada"),
            ("Tomate*", 388, "Tomatoes", "exacta"),
        ])
    )
    assert list(choques["item_codigo_fao"]) == [571]
    assert choques.iloc[0]["productos_sipsa"] == 2


def test_colisiones_reales_son_las_seis_documentadas():
    choques = homologacion.colisiones(homologacion.cargar())
    assert set(choques["item_codigo_fao"]) == {116, 463, 489, 497, 571, 603}
