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
        SELECT f.mercado FROM fact_precio_mayorista f
        LEFT JOIN dim_mercado d USING (mercado)
        WHERE d.mercado IS NULL
    """,
    "mayorista_sin_producto": """
        SELECT f.producto FROM fact_precio_mayorista f
        LEFT JOIN dim_producto_sipsa d USING (producto)
        WHERE d.producto IS NULL
    """,
    "mayorista_sin_periodo_en_tiempo": """
        SELECT f.periodo FROM fact_precio_mayorista f
        LEFT JOIN dim_tiempo t ON t.anio = f.anio AND t.mes = f.mes
        WHERE t.anio IS NULL
    """,
    "productor_sin_item": """
        SELECT f.item_codigo FROM fact_precio_productor f
        LEFT JOIN dim_item_fao d ON d.item_codigo = f.item_codigo
        WHERE d.item_codigo IS NULL
    """,
    "produccion_sin_item": """
        SELECT f.item_codigo FROM fact_produccion f
        LEFT JOIN dim_item_fao d ON d.item_codigo = f.item_codigo
        WHERE d.item_codigo IS NULL
    """,
    "comercio_sin_item": """
        SELECT f.item_codigo FROM fact_comercio f
        LEFT JOIN dim_item_fao d ON d.item_codigo = f.item_codigo
        WHERE d.item_codigo IS NULL
    """,
    "clima_sin_zona": """
        SELECT f.producto, f.departamento FROM fact_clima f
        LEFT JOIN dim_zona_productora d USING (producto, departamento)
        WHERE d.producto IS NULL
    """,
    "mayorista_clave_duplicada": """
        SELECT mercado, producto, periodo FROM fact_precio_mayorista
        GROUP BY 1, 2, 3 HAVING count(*) > 1
    """,
    "tiempo_clave_duplicada": """
        SELECT anio, mes FROM dim_tiempo GROUP BY 1, 2 HAVING count(*) > 1
    """,
    "puente_clave_duplicada": """
        SELECT producto_sipsa FROM puente_producto GROUP BY 1 HAVING count(*) > 1
    """,
    "precio_mayorista_no_positivo": """
        SELECT mercado, producto, periodo, precio_cop_kg FROM fact_precio_mayorista
        WHERE precio_cop_kg <= 0
    """,
    "precio_productor_negativo": """
        SELECT item_codigo, anio, valor FROM fact_precio_productor WHERE valor < 0
    """,
    "rango_de_precio_invertido": """
        SELECT mercado, producto, periodo FROM fact_precio_mayorista
        WHERE precio_min > precio_max
    """,
    "enso_fuera_de_rango": """
        SELECT anio, trimestre, anomalia FROM fact_enso
        WHERE anomalia < -5 OR anomalia > 5
    """,
    "mes_fuera_de_rango": """
        SELECT anio, mes FROM dim_tiempo WHERE mes NOT BETWEEN 1 AND 12
    """,
    # El puente solo debe marcar comparables los exactos: si una correspondencia
    # agregada se cuela como comparable, los margenes que se calculen son falsos.
    "puente_marca_comparable_lo_que_no_es": """
        SELECT producto_sipsa, tipo_correspondencia FROM puente_producto
        WHERE permite_comparar_precio AND tipo_correspondencia <> 'exacta'
    """,
    # Estos tres nacen de un error real: el puente clima-SIPSA se escribio con
    # nombres genericos ("Papa") que no existen en SIPSA ("Papa negra*"), asi que
    # el join corria sin error y unia cero filas. Un join vacio no se queja.
    "puente_zona_nombra_producto_inexistente": """
        SELECT p.producto_sipsa FROM puente_zona_sipsa p
        LEFT JOIN dim_producto_sipsa d ON d.producto = p.producto_sipsa
        WHERE d.producto IS NULL
    """,
    "puente_zona_apunta_a_zona_inexistente": """
        SELECT p.producto_zona, p.departamento FROM puente_zona_sipsa p
        LEFT JOIN dim_zona_productora z
               ON z.producto = p.producto_zona AND z.departamento = p.departamento
        WHERE z.producto IS NULL
    """,
    "el_cruce_clima_sipsa_no_une_nada": """
        SELECT 1 WHERE NOT EXISTS (
            SELECT 1
            FROM fact_precio_mayorista f
            JOIN puente_zona_sipsa p ON p.producto_sipsa = f.producto
            JOIN fact_clima c ON c.producto = p.producto_zona
                             AND c.departamento = p.departamento
                             AND c.anio = f.anio AND c.mes = f.mes
        )
    """,
}


def correr_chequeos(con: duckdb.DuckDBPyConnection) -> dict[str, Resultado]:
    """Corre todos los chequeos y devuelve el resultado de cada uno."""
    salida: dict[str, Resultado] = {}
    for nombre, consulta in CHEQUEOS.items():
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
