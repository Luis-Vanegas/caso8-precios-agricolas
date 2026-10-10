"""Tests de la limpieza de las fuentes nuevas (SIPSA semanal, abastecimiento y
Open-Meteo). Ninguno toca la red: usan las fixtures reales de adquisicion.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cleaning import clima_open_meteo, sipsa_canasta

FIXTURES = Path(__file__).parent / "fixtures"


def _carpeta_con(tmp_path: Path, dia: str, fixture: str, nombre: str) -> Path:
    """Simula data/raw/<fuente>/<dia>/ con una fixture adentro."""
    carpeta = tmp_path / dia
    carpeta.mkdir(parents=True)
    shutil.copy(FIXTURES / fixture, carpeta / nombre)
    return carpeta


# --- SIPSA semanal -------------------------------------------------------------

def test_unidad_sigue_la_metodologia_del_dane():
    nombres = pd.Series(["Huevo rojo AA", "Aceite girasol", "Papa criolla limpia", "Bocadillo veleño", "Vinagre"])
    assert sipsa_canasta.unidad(nombres).tolist() == ["unidad", "litro", "kg", "unidad", "litro"]


def test_semanal_trae_unidad_mercado_y_departamento(tmp_path):
    _carpeta_con(tmp_path, "2026-10-09", "sipsa_semanal.xml", "promediosSipsaSemanaMadr.xml")
    df = sipsa_canasta.limpiar_semanal(tmp_path)

    huevo = df[df["articulo"] == "Huevo rojo AA"].iloc[0]
    assert huevo["unidad"] == "unidad"            # precio de UN huevo, no de un kilo
    assert huevo["precio"] == 420
    assert huevo["departamento"] == "Quindio"     # Armenia, Mercar
    assert huevo["dpto_codigo"] == "63"
    assert huevo["periodo"] == 202511

    papa = df[df["articulo"] == "Papa criolla limpia"].iloc[0]
    assert papa["art_id"] == 159
    assert papa["dpto_codigo"] == "81"            # Arauca (Arauca)


def test_semanal_une_las_fotos_y_gana_la_mas_reciente():
    clave = {"art_id": 159, "fuen_id": 1, "semana_inicio": pd.Timestamp("2026-10-03")}
    vieja = pd.DataFrame([{**clave, "precio": 5000.0, "descarga": "2026-10-09"}])
    nueva = pd.DataFrame([{**clave, "precio": 5100.0, "descarga": "2026-10-16"},
                          {**clave, "semana_inicio": pd.Timestamp("2026-10-10"), "precio": 5200.0,
                           "descarga": "2026-10-16"}])
    unida = sipsa_canasta.unir_fotos([vieja, nueva])
    assert len(unida) == 2                         # la semana repetida queda una sola vez
    assert unida.loc[unida["semana_inicio"] == pd.Timestamp("2026-10-03"), "precio"].item() == 5100.0


# --- SIPSA abastecimiento -------------------------------------------------------

def test_abastecimiento_en_toneladas_con_departamento(tmp_path):
    _carpeta_con(tmp_path, "2026-10-09", "sipsa_abastecimiento.xml", "promedioAbasSipsaMesMadr.xml")
    df = sipsa_canasta.limpiar_abastecimiento(tmp_path)

    papa = df[df["articulo"] == "Papa criolla"].iloc[0]
    assert papa["toneladas"] == 6385
    assert papa["departamento"] == "Bogota"       # Bogota, D.C., Corabastos
    assert papa["dpto_codigo"] == "11"
    assert papa["periodo"] == 202607
    # Sin catalogo homologado todavia, las columnas existen pero van vacias
    assert {"producto", "grupo_dane"} <= set(df.columns)


# --- Open-Meteo -------------------------------------------------------------------

def test_clima_diario_observado_y_pronostico(tmp_path):
    carpeta = _carpeta_con(tmp_path, "2026-10-09", "open_meteo_observado.json", "observado_Boyaca.json")
    shutil.copy(FIXTURES / "open_meteo_pronostico.json", carpeta / "pronostico_Boyaca.json")
    df = clima_open_meteo.limpiar_diario(tmp_path)

    assert set(df["tipo"]) == {"observado", "pronostico"}
    assert len(df) == 6
    assert (df["dpto_codigo"] == "15").all()
    assert df.loc[df["fecha"] == pd.Timestamp("2026-10-08"), "precipitacion_mm"].item() == 8.0


def test_estacional_descarta_meses_incompletos(tmp_path):
    # La fixture real solo trae 4 dias: ningun mes esta completo
    _carpeta_con(tmp_path, "2026-10-09", "open_meteo_estacional.json", "estacional_Boyaca.json")
    assert clima_open_meteo.limpiar_estacional(tmp_path).empty


def test_estacional_percentiles_de_un_mes_completo():
    # Febrero de 2027 completo (28 dias) con 3 escenarios que llueven 1, 2 y 3 mm diarios
    dias = pd.date_range("2027-02-01", "2027-02-28").strftime("%Y-%m-%d").tolist()
    respuesta = {"daily": {"time": dias,
                           "precipitation_sum": [1.0] * 28,
                           "precipitation_sum_member01": [2.0] * 28,
                           "precipitation_sum_member02": [3.0] * 28}}
    df = clima_open_meteo.estacional_mensual(respuesta, "Boyaca")
    fila = df.iloc[0]
    assert fila["periodo"] == 202702
    assert fila["precip_p50"] == 56.0              # 2 mm x 28 dias
    assert fila["precip_p10"] < fila["precip_p50"] < fila["precip_p90"]


# --- Carpetas vacias (bug real del 2026-10-08) -------------------------------------

def test_carpeta_vacia_mas_nueva_no_tapa_la_buena(tmp_path):
    # Una descarga fallida deja la carpeta del dia vacia: hay que saltarla
    _carpeta_con(tmp_path, "2026-10-08", "sipsa_abastecimiento.xml", "promedioAbasSipsaMesMadr.xml")
    (tmp_path / "2026-10-09").mkdir()
    from src.common.rutas import carpetas_con_datos
    assert [c.name for c in carpetas_con_datos(tmp_path)] == ["2026-10-08"]
    assert len(sipsa_canasta.limpiar_abastecimiento(tmp_path)) == 3


def test_descarga_parcial_no_borra_archivos_buenos_de_dias_anteriores(tmp_path):
    # Bug real del 2026-10-09: IDEAM fallo en 3 archivos y la lluvia de esos
    # departamentos-anio desaparecio, aunque estaban sanos en la descarga anterior.
    from src.common.rutas import archivos_mas_recientes
    viejo, nuevo = tmp_path / "2026-09-23", tmp_path / "2026-10-09"
    viejo.mkdir(); nuevo.mkdir()
    (viejo / "lluvia_Antioquia_2025.json").write_text("viejo")
    (viejo / "lluvia_Boyaca_2025.json").write_text("viejo")
    (nuevo / "lluvia_Boyaca_2025.json").write_text("nuevo")      # Antioquia fallo hoy
    archivos = {a.name: a.read_text() for a in archivos_mas_recientes(tmp_path, "*.json")}
    assert archivos == {"lluvia_Antioquia_2025.json": "viejo", "lluvia_Boyaca_2025.json": "nuevo"}
