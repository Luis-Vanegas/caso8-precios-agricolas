"""Acceso a datos para la app. Unico lugar que abre la base.

Todo va con cache: DuckDB es rapido, pero Streamlit reejecuta el script entero
en cada interaccion y sin cache se releeria la base en cada clic.

La base se abre en solo lectura. La app nunca escribe.
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.rutas import BASE_DUCKDB, CONFIG

TTL = 3600  # segundos


@st.cache_resource
def conexion() -> duckdb.DuckDBPyConnection:
    """Conexion de solo lectura, compartida por toda la sesion."""
    if not BASE_DUCKDB.exists():
        st.error(
            f"No existe {BASE_DUCKDB.name}. Correr `python scripts/integrar.py` "
            "despues de `carga_inicial.py` y `preparar.py`."
        )
        st.stop()
    return duckdb.connect(str(BASE_DUCKDB), read_only=True)


@st.cache_data(ttl=TTL)
def consultar(sql: str) -> pd.DataFrame:
    """Ejecuta una consulta y devuelve un DataFrame cacheado."""
    return conexion().execute(sql).df()


@st.cache_data(ttl=TTL)
def precios_mayoristas() -> pd.DataFrame:
    return consultar("SELECT * FROM fact_precio_mayorista")


@st.cache_data(ttl=TTL)
def con_indicadores() -> pd.DataFrame:
    """Precios mayoristas con retorno, volatilidad y semaforo ya calculados."""
    from src.indicators.volatilidad import alertas

    return alertas(precios_mayoristas())


@st.cache_data(ttl=TTL)
def frescura() -> pd.DataFrame:
    """Ultima descarga por fuente. Alimenta el panel de frescura."""
    return consultar(
        """
        SELECT fuente, ultimo_periodo, fecha_descarga,
               fecha_actualizacion_fuente, estado, filas, mensaje
        FROM meta_actualizacion
        QUALIFY ROW_NUMBER() OVER (PARTITION BY fuente ORDER BY fecha_descarga DESC) = 1
        ORDER BY fuente
        """
    )


@st.cache_data(ttl=TTL)
def puente() -> pd.DataFrame:
    return consultar("SELECT * FROM puente_producto ORDER BY producto_sipsa")


@st.cache_data(ttl=TTL)
def enso() -> pd.DataFrame:
    return consultar("SELECT * FROM fact_enso ORDER BY anio, mes")


@st.cache_data(ttl=TTL)
def clima() -> pd.DataFrame:
    return consultar("SELECT * FROM fact_clima ORDER BY anio, mes")


def aviso_cache() -> None:
    """Nota fija: la app siempre lee de DuckDB, nunca llama a las APIs en vivo.

    Es una decision de diseño, no una limitacion: si una fuente esta caida, la
    app sigue funcionando y el panel de frescura dice cuan viejo es el dato.
    """
    st.caption(
        "La app lee del archivo DuckDB versionado, no de las APIs en vivo. "
        "El panel de frescura indica la antigüedad de cada fuente."
    )


# --- Ayudas para las paginas rediseñadas ------------------------------------


def fecha(periodo: int) -> str:
    """202608 -> 'ago 2026'. Mas facil de leer que el numero."""
    meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
    return f"{meses[periodo % 100 - 1]} {periodo // 100}"


@st.cache_data(ttl=TTL)
def ultimo_mes_cerrado() -> int:
    """Ultimo periodo AAAAMM cuyo mes ya termino.

    El mes en curso tiene pocos dias de dato y su promedio todavia cambia, asi
    que la portada muestra el ultimo mes completo. Si la base es anterior a la
    columna `mes_cerrado`, usa el ultimo periodo disponible.
    """
    columnas = consultar("DESCRIBE fact_precio_mayorista")["column_name"].tolist()
    filtro = "WHERE mes_cerrado" if "mes_cerrado" in columnas else ""
    return int(consultar(f"SELECT max(periodo) AS p FROM fact_precio_mayorista {filtro}")["p"][0])


@st.cache_data(ttl=TTL)
def mercados_geo() -> pd.DataFrame:
    """Coordenadas aproximadas (centro urbano) de cada mercado, para el mapa."""
    return pd.read_csv(CONFIG / "mercados.csv")


@st.cache_data(ttl=TTL)
def tabla_existe(nombre: str) -> bool:
    """True si la tabla esta en la base. Sirve para fuentes que aun no se cargaron."""
    return bool(consultar(
        f"SELECT count(*) AS n FROM duckdb_tables() WHERE table_name = '{nombre}'"
    )["n"][0])
