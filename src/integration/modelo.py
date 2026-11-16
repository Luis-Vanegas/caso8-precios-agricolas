"""Modelo de datos en DuckDB, construido con SQL sobre los parquet de interim.

DuckDB lee parquet directo, asi que no hay que pasar los datos por pandas para
cargarlos. Cada sentencia es un CREATE TABLE AS SELECT.

El nombre de cada tabla dice de donde viene el dato:

- `catalogo_`  listas de referencia (productos, mercados, zonas productoras).
- `col_`       dato medido en Colombia (SIPSA del DANE, sensores del IDEAM).
- `mundo_`     dato de una fuente internacional (FAO, NASA, NOAA, Banco Mundial,
               Open-Meteo), aunque hable de Colombia.
- `resultado_` lo que calcula este proyecto (las crea scripts/integrar.py).

Decision de diseño: SIPSA y FAOSTAT nombran los productos distinto y miden cosas
distintas. `catalogo_producto` tiene una fila por producto de SIPSA y dice cual
es su item equivalente en FAO y que tan valida es esa equivalencia. Solo las
filas con `permite_comparar_precio` sirven para comparar precio mayorista contra
precio al productor; las demas ubican el producto, no calculan margenes.

El diccionario completo esta en docs/diccionario_datos.md.
"""

from __future__ import annotations

import logging

import duckdb

from src.common.rutas import CONFIG, INTERMEDIO

log = logging.getLogger(__name__)

# Los codigos de mes de FAOSTAT son 7000 + numero de mes; 7021 es el agregado anual.
_MES_FAO = "(mes_codigo - 7000)"

# Los fertilizantes del Pink Sheet (Banco Mundial). El archivo trae 71 materias
# primas (petroleo, te, madera...); solo estas son insumo de los cultivos.
_FERTILIZANTES = ("Urea", "DAP", "TSP", "Potassium chloride **", "Phosphate rock")

# Codigos de calidad de FAOSTAT traducidos a palabras, para no obligar a nadie
# a memorizar que significa una letra.
_CALIDAD_FAO = """CASE flag WHEN 'A' THEN 'oficial'
                           WHEN 'E' THEN 'estimado'
                           WHEN 'I' THEN 'imputado'
                           WHEN 'X' THEN 'organismo internacional'
                           ELSE 'otro (' || coalesce(flag, 'sin codigo') || ')' END"""


def _p(ruta: str) -> str:
    """Ruta a un parquet de interim, lista para meter en el SQL."""
    return f"read_parquet('{(INTERMEDIO / ruta).as_posix()}')"


def _c(archivo: str) -> str:
    """Un CSV de config/ leido como texto, para no perder el cero de '05'."""
    return f"read_csv('{(CONFIG / archivo).as_posix()}', all_varchar = true)"


def _fao(archivo: str, dominio: str, mes: str = "NULL::INTEGER") -> str:
    """Un dominio de FAOSTAT con las mismas columnas que los otros cuatro.

    Los cinco dominios llegan con la misma forma, asi que se apilan en una sola
    tabla y la columna `dominio` dice de cual viene cada fila.
    """
    return f"""
        SELECT '{dominio}' AS dominio, item_codigo, item, elemento_codigo, elemento,
               unidad, anio, {mes} AS mes, valor, {_CALIDAD_FAO} AS calidad_dato
        FROM {_p(archivo)}
        WHERE valor IS NOT NULL"""


# El orden importa: los catalogos antes que los datos.
SENTENCIAS: dict[str, str] = {
    # --- Catalogos ----------------------------------------------------------
    # El departamento y su codigo DANE son la llave del mapa (une con el GeoJSON).
    "catalogo_mercado": f"""
        SELECT s.mercado, s.productos_con_precio, m.departamento, d.dpto_codigo
        FROM (
            SELECT mercado, count(*) AS productos_con_precio
            FROM (SELECT DISTINCT mercado, producto FROM {_p('sipsa/sipsa_mensual.parquet')})
            GROUP BY mercado
        ) s
        LEFT JOIN {_c('mercados.csv')} m ON m.mercado = s.mercado
        LEFT JOIN {_c('departamentos.csv')} d ON d.departamento = m.departamento
        ORDER BY s.mercado
    """,

    # Una fila por producto de SIPSA. Las columnas *_fao son el puente con
    # FAOSTAT, y llevan escrito cuanto se puede confiar en cada equivalencia.
    "catalogo_producto": f"""
        SELECT DISTINCT producto, producto_codigo,
               item_codigo_fao, item_fao, tipo_correspondencia,
               tipo_correspondencia = 'exacta' AS permite_comparar_precio
        FROM {_p('sipsa/sipsa_mensual.parquet')}
        ORDER BY producto
    """,

    # Donde se cultiva cada producto y con que nombre aparece en SIPSA.
    #
    # Una zona sirve a varios productos de SIPSA (papa negra y papa criolla
    # comparten zona) y un producto puede tener varias zonas. Las zonas que no
    # tienen precio en SIPSA (arroz, cafe) quedan con producto_sipsa vacio.
    #
    # Sin la columna producto_sipsa el cruce clima-SIPSA devuelve CERO filas,
    # porque la zona dice "Papa" donde SIPSA dice "Papa negra*". Fallo
    # silencioso: el join corre sin error y no une nada.
    "catalogo_zona_productora": f"""
        SELECT p.producto_sipsa,
               coalesce(z.producto, p.producto_zona) AS producto_zona,
               coalesce(z.departamento, p.departamento) AS departamento,
               z.lat, z.lon
        FROM (SELECT DISTINCT producto, departamento, lat, lon FROM {_p('clima/clima.parquet')}) z
        FULL JOIN {_p('zonas/zonas_puente.parquet')} p
               ON p.producto_zona = z.producto AND p.departamento = z.departamento
        ORDER BY producto_zona, departamento, producto_sipsa
    """,

    # --- Colombia: precio mayorista (SIPSA, DANE) ---------------------------
    # Ningun precio se imputa: un mes sin dato no tiene fila.
    "col_precio_mayorista_mensual": f"""
        SELECT mercado, producto, anio, mes, anio * 100 + mes AS periodo,
               precio_cop_kg, precio_min, precio_max, dias_con_dato,
               item_codigo_fao, tipo_correspondencia, mes_cerrado
        FROM {_p('sipsa/sipsa_mensual.parquet')}
    """,

    # --- Mundo: los cinco dominios de FAOSTAT para Colombia -----------------
    # `producto_en_sipsa` marca los items que tienen un producto equivalente con
    # precio mayorista; los balances usan codigos agregados y no enlazan.
    "mundo_fao_colombia": f"""
        SELECT f.*,
               f.item_codigo IN (
                   SELECT DISTINCT item_codigo_fao FROM {_p('sipsa/sipsa_mensual.parquet')}
                   WHERE item_codigo_fao IS NOT NULL
               ) AS producto_en_sipsa
        FROM (
            {_fao('faostat/faostat_pp.parquet', 'precio_productor',
                  f"CASE WHEN frecuencia = 'mensual' THEN {_MES_FAO} END")}
            UNION ALL {_fao('faostat/faostat_qcl.parquet', 'produccion')}
            UNION ALL {_fao('faostat/faostat_tcl.parquet', 'comercio')}
            UNION ALL {_fao('faostat/faostat_fbs.parquet', 'balance_alimentario')}
            UNION ALL {_fao('faostat/faostat_qv.parquet', 'valor_produccion')}
        ) f
    """,

    # --- Mundo: clima e insumos ---------------------------------------------
    "mundo_clima_zona_mensual": f"""
        SELECT producto, departamento, anio, mes, anio * 100 + mes AS periodo,
               PRECTOTCORR AS precipitacion_mm_dia,
               T2M AS temperatura_c,
               PRECTOTCORR_anomalia AS precipitacion_anomalia,
               fuente, dias_con_dato
        FROM {_p('clima/clima.parquet')}
    """,

    "mundo_fenomeno_nino": f"""
        SELECT anio, trimestre, mes_central AS mes, anomalia, fase, provisional
        FROM {_p('enso/enso.parquet')}
    """,

    "mundo_precio_fertilizantes": f"""
        SELECT commodity AS insumo, unidad, anio, mes, anio * 100 + mes AS periodo, valor_usd
        FROM {_p('insumos/insumos.parquet')}
        WHERE valor_usd IS NOT NULL AND commodity IN {_FERTILIZANTES}
    """,
}


# Tablas de fuentes que pueden no estar descargadas todavia. Se construyen solo si
# su parquet existe, para que el modelo no se caiga por una fuente nueva.
OPCIONALES: dict[str, tuple[str, str]] = {
    # La estacion es la unidad fisica de captura: codigo, sensor y ubicacion.
    "col_estacion_ideam": ("ideam/ideam_estaciones.parquet", f"""
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
    # Mismo grano que mundo_clima_zona_mensual (departamento, anio, mes): esa es
    # la variable de integracion entre el sensor y el resto del modelo.
    "col_sensor_ideam_mensual": ("ideam/ideam_depto.parquet", f"""
        SELECT variable, departamento, anio, mes, anio * 100 + mes AS periodo,
               valor, anomalia, n_estaciones
        FROM {_p('ideam/ideam_depto.parquet')}
    """),

    # --- Fase clima -> oferta -> precio (ver docs/contrato_datos.md) ----------
    # Llave del articulo: art_id. Nunca se promedian articulos distintos.
    "col_precio_mayorista_semanal": ("sipsa/sipsa_semanal.parquet", f"""
        SELECT mercado, ciudad, departamento, dpto_codigo, fuen_id,
               art_id, articulo, producto, grupo_dane, en_canasta,
               semana_inicio, anio, mes, periodo,
               precio, precio_min, precio_max, unidad
        FROM {_p('sipsa/sipsa_semanal.parquet')}
    """),
    "col_abastecimiento_mensual": ("sipsa/sipsa_abastecimiento.parquet", f"""
        SELECT mercado, ciudad, departamento, dpto_codigo, fuen_id,
               art_id, articulo, producto, grupo_dane,
               anio, mes, periodo, toneladas
        FROM {_p('sipsa/sipsa_abastecimiento.parquet')}
    """),
    "mundo_clima_diario": ("clima/clima_diario.parquet", f"""
        SELECT departamento, dpto_codigo, fecha, precipitacion_mm,
               temp_max, temp_min, tipo, fuente
        FROM {_p('clima/clima_diario.parquet')}
    """),
    "mundo_pronostico_lluvia": ("clima/clima_estacional.parquet", f"""
        SELECT * FROM {_p('clima/clima_estacional.parquet')}
    """),
}

# Prefijos de los nombres que tenia el modelo antes de reorganizarlo. Una base
# construida con la version anterior los conserva, porque CREATE OR REPLACE solo
# toca las tablas que nombra; por eso se borran al reconstruir.
_PREFIJOS_VIEJOS = ("dim_", "fact_", "puente_", "indicador_")


def borrar_tablas_viejas(con: duckdb.DuckDBPyConnection) -> list[str]:
    """Borra las tablas con nombres de la version anterior. Devuelve cuales borro."""
    nombres = [f[0] for f in con.execute("SELECT table_name FROM duckdb_tables()").fetchall()]
    viejas = [n for n in nombres if n.startswith(_PREFIJOS_VIEJOS) or n == "pronostico_precio"]
    for nombre in viejas:
        con.execute(f'DROP TABLE "{nombre}"')
    return viejas


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
    for nombre in borrar_tablas_viejas(con):
        log.info("%-28s borrada (nombre anterior)", nombre)
    for tabla, consulta in SENTENCIAS.items():
        con.execute(f"CREATE OR REPLACE TABLE {tabla} AS {consulta}")
        conteos[tabla] = con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]
        log.info("%-28s %8d filas", tabla, conteos[tabla])
    for tabla, (parquet, consulta) in OPCIONALES.items():
        if not (INTERMEDIO / parquet).exists():
            log.warning("%-28s omitida: falta %s", tabla, parquet)
            continue
        con.execute(f"CREATE OR REPLACE TABLE {tabla} AS {consulta}")
        conteos[tabla] = con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0]
        log.info("%-28s %8d filas", tabla, conteos[tabla])
    return conteos
