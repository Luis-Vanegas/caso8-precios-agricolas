"""Chequeos de integridad del modelo estrella.

Cargar sin errores no significa que el modelo este bien. Estos chequeos buscan
las formas concretas en que un modelo estrella se rompe en silencio: un hecho
que apunta a una dimension inexistente, una clave que se duplico al unir, o una
regla de negocio que dejo de cumplirse.

Cada chequeo devuelve OK o FALLA con el detalle, y `integrar.py` sale con codigo
distinto de cero si alguno falla.
"""

from __future__ import annotations

from dataclasses import dataclass

import duckdb


@dataclass(frozen=True)
class Resultado:
    ok: bool
    detalle: str


# Cada chequeo es una consulta que debe devolver CERO filas. Si devuelve
# alguna, esa fila es el problema.
CHEQUEOS: dict[str, str] = {
    "mayorista_sin_mercado": """
        SELECT f.mercado FROM col_precio_mayorista_mensual f
        LEFT JOIN catalogo_mercado d USING (mercado)
        WHERE d.mercado IS NULL
    """,
    "mayorista_sin_producto": """
        SELECT f.producto FROM col_precio_mayorista_mensual f
        LEFT JOIN catalogo_producto d USING (producto)
        WHERE d.producto IS NULL
    """,
    # `periodo` es la unica columna de tiempo que cruza tablas (anio * 100 + mes):
    # si no coincide con anio y mes, los cruces por periodo unen meses distintos.
    "mayorista_periodo_incoherente": """
        SELECT anio, mes, periodo FROM col_precio_mayorista_mensual
        WHERE periodo <> anio * 100 + mes
    """,
    # Los cinco dominios de FAOSTAT que pide el reto tienen que estar todos.
    "fao_dominio_faltante": """
        SELECT d.dominio
        FROM (VALUES ('precio_productor'), ('produccion'), ('comercio'),
                     ('balance_alimentario'), ('valor_produccion')) d(dominio)
        WHERE d.dominio NOT IN (SELECT DISTINCT dominio FROM mundo_fao_colombia)
    """,
    "fao_item_sin_nombre": """
        SELECT DISTINCT dominio, item_codigo FROM mundo_fao_colombia WHERE item IS NULL
    """,
    # Un codigo de calidad nuevo de FAO que nadie tradujo queda como 'otro (...)'.
    "fao_calidad_sin_traducir": """
        SELECT DISTINCT calidad_dato FROM mundo_fao_colombia WHERE calidad_dato LIKE 'otro%'
    """,
    "clima_sin_zona": """
        SELECT DISTINCT f.producto, f.departamento FROM mundo_clima_zona_mensual f
        LEFT JOIN catalogo_zona_productora d
               ON d.producto_zona = f.producto AND d.departamento = f.departamento
        WHERE d.producto_zona IS NULL
    """,
    "mayorista_clave_duplicada": """
        SELECT mercado, producto, periodo FROM col_precio_mayorista_mensual
        GROUP BY 1, 2, 3 HAVING count(*) > 1
    """,
    "zona_clave_duplicada": """
        SELECT producto_sipsa, producto_zona, departamento FROM catalogo_zona_productora
        GROUP BY ALL HAVING count(*) > 1
    """,
    "producto_clave_duplicada": """
        SELECT producto FROM catalogo_producto GROUP BY 1 HAVING count(*) > 1
    """,
    "precio_mayorista_no_positivo": """
        SELECT mercado, producto, periodo, precio_cop_kg FROM col_precio_mayorista_mensual
        WHERE precio_cop_kg <= 0
    """,
    "precio_productor_negativo": """
        SELECT item_codigo, anio, valor FROM mundo_fao_colombia
        WHERE dominio = 'precio_productor' AND valor < 0
    """,
    "rango_de_precio_invertido": """
        SELECT mercado, producto, periodo FROM col_precio_mayorista_mensual
        WHERE precio_min > precio_max
    """,
    "enso_fuera_de_rango": """
        SELECT anio, trimestre, anomalia FROM mundo_fenomeno_nino
        WHERE anomalia < -5 OR anomalia > 5
    """,
    "mes_fuera_de_rango": """
        SELECT DISTINCT anio, mes FROM col_precio_mayorista_mensual
        WHERE mes NOT BETWEEN 1 AND 12
    """,
    # El catalogo solo debe marcar comparables los exactos: si una correspondencia
    # agregada se cuela como comparable, los margenes que se calculen son falsos.
    "producto_marca_comparable_lo_que_no_es": """
        SELECT producto, tipo_correspondencia FROM catalogo_producto
        WHERE permite_comparar_precio AND tipo_correspondencia <> 'exacta'
    """,
    # Estos tres nacen de un error real: el puente clima-SIPSA se escribio con
    # nombres genericos ("Papa") que no existen en SIPSA ("Papa negra*"), asi que
    # el join corria sin error y unia cero filas. Un join vacio no se queja.
    "zona_nombra_producto_inexistente": """
        SELECT p.producto_sipsa FROM catalogo_zona_productora p
        LEFT JOIN catalogo_producto d ON d.producto = p.producto_sipsa
        WHERE p.producto_sipsa IS NOT NULL AND d.producto IS NULL
    """,
    # Una zona sin coordenadas es una que esta en la configuracion pero no tiene
    # clima descargado: el producto quedaria sin lluvia que cruzar.
    "zona_sin_clima_descargado": """
        SELECT producto_zona, departamento FROM catalogo_zona_productora
        WHERE lat IS NULL
    """,
    "el_cruce_clima_sipsa_no_une_nada": """
        SELECT 1 WHERE NOT EXISTS (
            SELECT 1
            FROM col_precio_mayorista_mensual f
            JOIN catalogo_zona_productora p ON p.producto_sipsa = f.producto
            JOIN mundo_clima_zona_mensual c ON c.producto = p.producto_zona
                             AND c.departamento = p.departamento
                             AND c.anio = f.anio AND c.mes = f.mes
        )
    """,
    # El mapa une por codigo DANE: un mercado sin codigo queda fuera del mapa.
    "mercado_sin_codigo_de_departamento": """
        SELECT mercado FROM catalogo_mercado WHERE dpto_codigo IS NULL
    """,
}


# Chequeos de las tablas nuevas (fase clima -> oferta -> precio). Como esas tablas
# son opcionales en el modelo, cada chequeo corre solo si su tabla existe.
CHEQUEOS_OPCIONALES: dict[str, tuple[str, str]] = {
    "semanal_clave_duplicada": ("col_precio_mayorista_semanal", """
        SELECT art_id, fuen_id, semana_inicio FROM col_precio_mayorista_semanal
        GROUP BY ALL HAVING count(*) > 1
    """),
    "semanal_unidad_invalida": ("col_precio_mayorista_semanal", """
        SELECT DISTINCT unidad FROM col_precio_mayorista_semanal
        WHERE unidad IS NULL OR unidad NOT IN ('kg', 'unidad', 'litro')
    """),
    # Metodologia SIPSA-P: el huevo va por unidad. Marcarlo kg lo leeria mil veces mal.
    "semanal_huevo_que_no_va_por_unidad": ("col_precio_mayorista_semanal", """
        SELECT DISTINCT articulo FROM col_precio_mayorista_semanal
        WHERE lower(articulo) LIKE 'huevo%' AND unidad <> 'unidad'
    """),
    "semanal_precio_no_positivo": ("col_precio_mayorista_semanal", """
        SELECT art_id, fuen_id, semana_inicio FROM col_precio_mayorista_semanal WHERE precio <= 0
    """),
    "semanal_sin_departamento": ("col_precio_mayorista_semanal", """
        SELECT DISTINCT fuen_id FROM col_precio_mayorista_semanal WHERE dpto_codigo IS NULL
    """),
    "abastecimiento_clave_duplicada": ("col_abastecimiento_mensual", """
        SELECT art_id, fuen_id, anio, mes FROM col_abastecimiento_mensual
        GROUP BY ALL HAVING count(*) > 1
    """),
    "abastecimiento_toneladas_negativas": ("col_abastecimiento_mensual", """
        SELECT art_id, fuen_id, periodo FROM col_abastecimiento_mensual WHERE toneladas < 0
    """),
    "clima_diario_sin_codigo": ("mundo_clima_diario", """
        SELECT DISTINCT departamento FROM mundo_clima_diario WHERE dpto_codigo IS NULL
    """),
    "estacional_percentiles_desordenados": ("mundo_pronostico_lluvia", """
        SELECT departamento, periodo FROM mundo_pronostico_lluvia
        WHERE NOT (precip_p10 <= precip_p50 AND precip_p50 <= precip_p90)
    """),
}


def correr_chequeos(con: duckdb.DuckDBPyConnection) -> dict[str, Resultado]:
    """Corre todos los chequeos y devuelve el resultado de cada uno."""
    salida: dict[str, Resultado] = {}
    existentes = {fila[0] for fila in con.execute("SELECT table_name FROM duckdb_tables()").fetchall()}
    a_correr = dict(CHEQUEOS)
    a_correr.update({n: sql for n, (tabla, sql) in CHEQUEOS_OPCIONALES.items() if tabla in existentes})
    for nombre, consulta in a_correr.items():
        try:
            filas = con.execute(consulta).fetchall()
        except duckdb.Error as exc:
            salida[nombre] = Resultado(False, f"la consulta fallo: {exc}")
            continue
        salida[nombre] = Resultado(
            not filas,
            "sin problemas" if not filas else f"{len(filas)} filas problematicas, p.ej. {filas[0]}",
        )
    return salida
