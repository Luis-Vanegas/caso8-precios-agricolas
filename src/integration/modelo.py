"""Modelo estrella en DuckDB, construido con SQL sobre los parquet de interim.

DuckDB lee parquet directo, asi que no hay que pasar los datos por pandas para
cargarlos. Cada sentencia es un CREATE TABLE AS SELECT.

Decision de diseño: **dos dimensiones de producto, no una**.

SIPSA y FAOSTAT miden cosas distintas con vocabularios distintos. Forzarlos a
una sola dimension obliga a elegir un grano y pierde el otro. En su lugar hay
`dim_producto_sipsa` (33 productos comerciales colombianos) y `dim_item_fao`
(items de la clasificacion internacional), unidos por `puente_producto`, que
declara explicitamente que tan valida es cada correspondencia.

Consecuencia practica: solo las filas del puente con `tipo_correspondencia =
'exacta'` habilitan comparar precio mayorista contra precio productor. Las
demas sirven para ubicar el producto en la jerarquia, no para calcular margenes.
"""

from __future__ import annotations

import logging

import duckdb

from src.common.rutas import CONFIG, INTERMEDIO

log = logging.getLogger(__name__)

# Los codigos de mes de FAOSTAT son 7000 + numero de mes; 7021 es el agregado anual.
_MES_FAO = "(mes_codigo - 7000)"


def _p(ruta: str) -> str:
    """Ruta a un parquet de interim, lista para meter en el SQL."""
    return f"read_parquet('{(INTERMEDIO / ruta).as_posix()}')"


def _c(archivo: str) -> str:
    """Un CSV de config/ leido como texto, para no perder el cero de '05'."""
    return f"read_csv('{(CONFIG / archivo).as_posix()}', all_varchar = true)"


# El orden importa: las dimensiones antes que los hechos.
SENTENCIAS: dict[str, str] = {
    # --- Dimensiones --------------------------------------------------------
    "dim_tiempo": f"""
        SELECT DISTINCT anio, mes,
               anio * 100 + mes AS periodo,
               CAST(anio || '-' || lpad(CAST(mes AS VARCHAR), 2, '0') || '-01' AS DATE) AS primer_dia
        FROM (
            SELECT anio, mes FROM {_p('sipsa/sipsa_mensual.parquet')}
            UNION
            SELECT anio, {_MES_FAO} AS mes FROM {_p('faostat/faostat_pp.parquet')}
                WHERE frecuencia = 'mensual'
            UNION
            SELECT anio, mes FROM {_p('clima/clima.parquet')}
            UNION
            SELECT anio, mes FROM {_p('insumos/insumos.parquet')}
        )
        WHERE anio IS NOT NULL AND mes BETWEEN 1 AND 12
        ORDER BY anio, mes
    """,

    # El departamento y su codigo DANE son la llave del mapa (une con el GeoJSON).
    "dim_mercado": f"""
        SELECT s.mercado, s.series, m.departamento, d.dpto_codigo
        FROM (
            SELECT mercado, count(*) AS series
            FROM (SELECT DISTINCT mercado, producto FROM {_p('sipsa/sipsa_mensual.parquet')})
            GROUP BY mercado
        ) s
        LEFT JOIN {_c('mercados.csv')} m ON m.mercado = s.mercado
        LEFT JOIN {_c('departamentos.csv')} d ON d.departamento = m.departamento
        ORDER BY s.mercado
    """,

    "dim_producto_sipsa": f"""
        SELECT DISTINCT producto, producto_codigo,
               item_codigo_fao, item_fao, tipo_correspondencia
        FROM {_p('sipsa/sipsa_mensual.parquet')}
        ORDER BY producto
    """,

    "dim_item_fao": f"""
        SELECT item_codigo, any_value(item) AS item, any_value(item_cpc) AS item_cpc,
               bool_or(dominio = 'PP') AS tiene_precio_productor,
               bool_or(dominio = 'QCL') AS tiene_produccion,
               bool_or(dominio = 'TCL') AS tiene_comercio
        FROM (
            SELECT item_codigo, item, item_cpc, dominio FROM {_p('faostat/faostat_pp.parquet')}
            UNION ALL
            SELECT item_codigo, item, item_cpc, dominio FROM {_p('faostat/faostat_qcl.parquet')}
            UNION ALL
            SELECT item_codigo, item, item_cpc, dominio FROM {_p('faostat/faostat_tcl.parquet')}
        )
        GROUP BY item_codigo
        ORDER BY item_codigo
    """,

    # El puente es la unica via legitima entre los dos vocabularios, y lleva
    # escrito cuanto se puede confiar en cada fila.
    "puente_producto": f"""
        SELECT DISTINCT producto AS producto_sipsa, item_codigo_fao, item_fao,
               tipo_correspondencia,
               tipo_correspondencia = 'exacta' AS permite_comparar_precio
        FROM {_p('sipsa/sipsa_mensual.parquet')}
        ORDER BY producto_sipsa
    """,

    "dim_zona_productora": f"""
        SELECT DISTINCT producto, departamento, lat, lon, elevacion_grilla_m
        FROM {_p('clima/clima.parquet')}
        ORDER BY producto, departamento
    """,

    # Una zona climatica sirve a varios productos de SIPSA (papa negra y papa
    # criolla comparten zona) y un producto puede tener varias zonas: es una
    # relacion de muchos a muchos y por eso va en su propia tabla.
    #
    # Sin este puente el cruce clima-SIPSA devuelve CERO filas, porque la config
    # dice "Papa" donde SIPSA dice "Papa negra*". Fallo silencioso: el join
    # corre sin error y no une nada.
    "puente_zona_sipsa": f"""
        SELECT producto_sipsa, producto_zona, departamento
        FROM {_p('zonas/zonas_puente.parquet')}
        ORDER BY producto_sipsa, departamento
    """,

    # --- Hechos de precio (dos, a su propio grano) --------------------------
    "fact_precio_mayorista": f"""
        SELECT mercado, producto, anio, mes, anio * 100 + mes AS periodo,
               precio_cop_kg, precio_min, precio_max, dias_con_dato,
               item_codigo_fao, tipo_correspondencia, mes_cerrado,
               FALSE AS imputado
        FROM {_p('sipsa/sipsa_mensual.parquet')}
    """,

    "fact_precio_productor": f"""
        SELECT item_codigo, elemento_codigo, elemento, unidad, anio,
               CASE WHEN frecuencia = 'mensual' THEN {_MES_FAO} END AS mes,
               frecuencia, valor, flag,
               FALSE AS imputado
        FROM {_p('faostat/faostat_pp.parquet')}
        WHERE valor IS NOT NULL
    """,

    # --- Hechos anuales de FAOSTAT ------------------------------------------
    "fact_produccion": f"""
        SELECT item_codigo, elemento_codigo, elemento, unidad, anio, valor, flag,
               FALSE AS imputado
        FROM {_p('faostat/faostat_qcl.parquet')}
        WHERE valor IS NOT NULL
    """,

    "fact_comercio": f"""
        SELECT item_codigo, elemento_codigo, elemento, unidad, anio, valor, flag,
               FALSE AS imputado
        FROM {_p('faostat/faostat_tcl.parquet')}
        WHERE valor IS NOT NULL
    """,

    "fact_balance": f"""
        SELECT item_codigo, elemento_codigo, elemento, unidad, anio, valor, flag,
               FALSE AS imputado
        FROM {_p('faostat/faostat_fbs.parquet')}
        WHERE valor IS NOT NULL
    """,

    "fact_valor_produccion": f"""
        SELECT item_codigo, elemento_codigo, elemento, unidad, anio, valor, flag,
               FALSE AS imputado
        FROM {_p('faostat/faostat_qv.parquet')}
        WHERE valor IS NOT NULL
    """,

    "fact_tasa_cambio": f"""
        SELECT elemento_codigo, elemento, moneda_iso, unidad, anio,
               CASE WHEN frecuencia = 'mensual' THEN {_MES_FAO} END AS mes,
               frecuencia, valor, flag
        FROM {_p('faostat/faostat_pe.parquet')}
        WHERE valor IS NOT NULL
    """,

    # --- Hechos complementarios ---------------------------------------------
    "fact_clima": f"""
        SELECT producto, departamento, anio, mes, anio * 100 + mes AS periodo,
               PRECTOTCORR AS precipitacion_mm_dia,
               T2M AS temperatura_c,
               PRECTOTCORR_anomalia AS precipitacion_anomalia,
               fuente, dias_con_dato
        FROM {_p('clima/clima.parquet')}
    """,

    "fact_enso": f"""
        SELECT anio, trimestre, mes_central AS mes, anomalia, fase, provisional
        FROM {_p('enso/enso.parquet')}
    """,

    "fact_insumos": f"""
        SELECT commodity, unidad, anio, mes, anio * 100 + mes AS periodo, valor_usd
        FROM {_p('insumos/insumos.parquet')}
        WHERE valor_usd IS NOT NULL
    """,
}


# Tablas de fuentes que pueden no estar descargadas todavia. Se construyen solo si
# su parquet existe, para que el modelo no se caiga por una fuente nueva.
OPCIONALES: dict[str, tuple[str, str]] = {
    # La estacion es la unidad fisica de captura: codigo, sensor y ubicacion.
    "dim_estacion_ideam": ("ideam/ideam_estaciones.parquet", f"""
        SELECT codigoestacion, codigosensor,
               any_value(nombreestacion) AS nombre, any_value(departamento) AS departamento,
               any_value(municipio) AS municipio,
               any_value(latitud) AS lat, any_value(longitud) AS lon,
               list(DISTINCT variable) AS variables,
               round(avg(CAST(valido AS INTEGER)), 3) AS proporcion_meses_validos
        FROM {_p('ideam/ideam_estaciones.parquet')}
        GROUP BY codigoestacion, codigosensor
        ORDER BY departamento, codigoestacion
    """),
    # Mismo grano que fact_clima (departamento, anio, mes): esa es la variable de
    # integracion entre el sensor y el resto del modelo.
    "fact_sensor_ideam": ("ideam/ideam_depto.parquet", f"""
        SELECT variable, departamento, anio, mes, anio * 100 + mes AS periodo,
               valor, anomalia, n_estaciones
        FROM {_p('ideam/ideam_depto.parquet')}
    """),

    # --- Fase clima -> oferta -> precio (ver docs/contrato_datos.md) ----------
    # Llave del articulo: art_id. Nunca se promedian articulos distintos.
    "fact_precio_semanal": ("sipsa/sipsa_semanal.parquet", f"""
        SELECT mercado, ciudad, departamento, dpto_codigo, fuen_id,
               art_id, articulo, producto, grupo_dane, en_canasta,
               semana_inicio, anio, mes, periodo,
               precio, precio_min, precio_max, unidad
        FROM {_p('sipsa/sipsa_semanal.parquet')}
    """),
    "fact_abastecimiento": ("sipsa/sipsa_abastecimiento.parquet", f"""
        SELECT mercado, ciudad, departamento, dpto_codigo, fuen_id,
               art_id, articulo, producto, grupo_dane,
               anio, mes, periodo, toneladas
        FROM {_p('sipsa/sipsa_abastecimiento.parquet')}
    """),
    "fact_clima_diario": ("clima/clima_diario.parquet", f"""
        SELECT departamento, dpto_codigo, fecha, precipitacion_mm,
               temp_max, temp_min, tipo, fuente
        FROM {_p('clima/clima_diario.parquet')}
    """),
    "fact_pronostico_estacional": ("clima/clima_estacional.parquet", f"""
        SELECT * FROM {_p('clima/clima_estacional.parquet')}
    """),
}


def compactar(ruta) -> tuple[float, float]:
    """Reescribe la base en un archivo nuevo para recuperar el espacio muerto.

    `CREATE OR REPLACE TABLE` no libera las paginas de la version anterior, asi
    que el archivo crece en cada reconstruccion: medido, 16,5 MB contra 5,8 MB
    reescrito. Como este archivo se versiona en el repositorio, esa diferencia
    se acumularia en el historial de git.

    Devuelve el tamaño antes y despues, en megabytes.
    """
    antes = ruta.stat().st_size / 1e6
    temporal = ruta.with_suffix(".compactando")
    temporal.unlink(missing_ok=True)

    nueva = duckdb.connect(str(temporal))
    nueva.execute(f"ATTACH '{ruta}' AS vieja (READ_ONLY)")
    tablas = [
        fila[0]
        for fila in nueva.execute(
            "SELECT table_name FROM duckdb_tables() WHERE database_name = 'vieja'"
        ).fetchall()
    ]
    for tabla in tablas:
        nueva.execute(f'CREATE TABLE "{tabla}" AS SELECT * FROM vieja."{tabla}"')
    nueva.close()

    # replace() sobrescribe en un solo paso: si algo falla a la mitad, queda la
    # base vieja completa y no un hueco sin archivo.
    temporal.replace(ruta)
    return antes, ruta.stat().st_size / 1e6


def construir(con: duckdb.DuckDBPyConnection) -> dict[str, int]:
    """Crea o reemplaza todas las tablas del modelo. Devuelve el conteo de filas.

    `meta_actualizacion` no se toca: es historico y lo escribe `actualizar.py`.
    """
    conteos: dict[str, int] = {}
    for tabla, consulta in SENTENCIAS.items():
        con.execute(f"CREATE OR REPLACE TABLE {tabla} AS {consulta}")
        conteos[tabla] = con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]
        log.info("%-24s %8d filas", tabla, conteos[tabla])
    for tabla, (parquet, consulta) in OPCIONALES.items():
        if not (INTERMEDIO / parquet).exists():
            log.warning("%-24s omitida: falta %s", tabla, parquet)
            continue
        con.execute(f"CREATE OR REPLACE TABLE {tabla} AS {consulta}")
        conteos[tabla] = con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]
        log.info("%-24s %8d filas", tabla, conteos[tabla])
    return conteos
