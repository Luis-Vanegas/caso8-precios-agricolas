"""Tabla `meta_actualizacion` en DuckDB: bitacora de que se descargo y cuando.

Es la fuente de verdad para dos cosas: el panel de frescura de la app y la
deteccion de datos nuevos (comparar la fecha de actualizacion que reporta la
fuente contra la ultima registrada).
"""

from __future__ import annotations

from datetime import datetime, timezone

import duckdb

from src.common.modelos import ResultadoDescarga
from src.common.rutas import BASE_DUCKDB

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS meta_actualizacion (
    fuente                     VARCHAR   NOT NULL,
    ultimo_periodo             VARCHAR,
    fecha_descarga             TIMESTAMP NOT NULL,
    fecha_actualizacion_fuente TIMESTAMP,
    estado                     VARCHAR   NOT NULL,
    filas                      BIGINT,
    mensaje                    VARCHAR
);
"""


def conectar(ruta=None) -> duckdb.DuckDBPyConnection:
    """Abre la base y garantiza que la tabla de bitacora exista."""
    ruta = ruta or BASE_DUCKDB
    ruta.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(ruta))
    con.execute(_ESQUEMA)
    return con


def registrar(con: duckdb.DuckDBPyConnection, resultado: ResultadoDescarga) -> None:
    """Agrega una linea a la bitacora. Nunca borra ni actualiza: es historico."""
    con.execute(
        """
        INSERT INTO meta_actualizacion
            (fuente, ultimo_periodo, fecha_descarga,
             fecha_actualizacion_fuente, estado, filas, mensaje)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            resultado.fuente,
            resultado.ultimo_periodo,
            datetime.now(timezone.utc),
            resultado.fecha_actualizacion_fuente,
            resultado.estado,
            resultado.filas,
            resultado.mensaje,
        ],
    )


def ultima_actualizacion_fuente(
    con: duckdb.DuckDBPyConnection, fuente: str
) -> datetime | None:
    """Fecha de actualizacion reportada en la ultima descarga exitosa de esa fuente.

    Devuelve None si nunca se descargo con exito, que es lo que hace que la
    primera corrida siempre baje datos.
    """
    fila = con.execute(
        """
        SELECT fecha_actualizacion_fuente
        FROM meta_actualizacion
        WHERE fuente = ? AND estado = 'ok'
        ORDER BY fecha_descarga DESC
        LIMIT 1
        """,
        [fuente],
    ).fetchone()
    return fila[0] if fila else None


def resumen_frescura(con: duckdb.DuckDBPyConnection):
    """Una fila por fuente con su ultima descarga. Alimenta el panel de la app."""
    return con.execute(
        """
        SELECT fuente, ultimo_periodo, fecha_descarga,
               fecha_actualizacion_fuente, estado, filas, mensaje
        FROM meta_actualizacion
        QUALIFY ROW_NUMBER() OVER (PARTITION BY fuente ORDER BY fecha_descarga DESC) = 1
        ORDER BY fuente
        """
    ).fetchdf()
