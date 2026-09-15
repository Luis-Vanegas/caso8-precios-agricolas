"""Calidad de datos: homologación, frescura y limitaciones declaradas."""

from __future__ import annotations

import streamlit as st

from datos import aviso_cache, consultar, frescura, puente

st.set_page_config(page_title="Calidad de datos", page_icon="🔍", layout="wide")
st.title("🔍 Calidad de datos")

st.markdown(
    "Esta página existe porque **un dato sin su limitación declarada es un dato peligroso**. "
    "Todo lo que aparece acá salió de verificar contra las fuentes reales, no de suponer."
)

# --- Frescura ---------------------------------------------------------------

st.subheader("Frescura por fuente")
st.dataframe(frescura(), width="stretch", hide_index=True)
aviso_cache()

st.markdown(
    """
**Calendario esperado de actualización**

| Fuente | Frecuencia | Cuándo publica |
|---|---|---|
| SIPSA mayoristas | Diaria | 2:00 p.m. |
| SIPSA mensual | Mensual | Día 8 |
| SIPSA abastecimiento | Mensual | Día 10 |
| ONI (NOAA) | Mensual | Segundo jueves |
| Pink Sheet | Mensual | Inicio de mes |
| NASA POWER mensual | Por año cerrado | Con más de un año de rezago |
| FAOSTAT | Anual | FBS en octubre; PP, QCL y TCL en diciembre |
"""
)

# --- Homologación -----------------------------------------------------------

st.subheader("Homologación SIPSA ↔ FAOSTAT")

p = puente()
conteo = p["tipo_correspondencia"].value_counts()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Exactas", int(conteo.get("exacta", 0)))
c2.metric("Agregadas", int(conteo.get("agregada", 0)))
c3.metric("Genéricas", int(conteo.get("generica", 0)))
c4.metric("Sin equivalente", int(conteo.get("sin_equivalente", 0)))

st.error(
    "**Solo las correspondencias exactas permiten comparar precio mayorista contra precio "
    "productor.** En las agregadas, FAOSTAT mete varios productos de SIPSA en un mismo ítem: "
    "guayaba y mango tommy comparten el ítem 571; limón común y limón Tahití comparten el 497. "
    "El precio de FAO para esos ítems es una mezcla y no corresponde a ningún producto por "
    "separado. Calcular un margen contra él produce un número que parece razonable y es falso."
)

st.dataframe(p, width="stretch", hide_index=True)

colisiones = consultar(
    """
    SELECT item_codigo_fao, any_value(item_fao) AS item_fao,
           count(*) AS productos_sipsa,
           string_agg(producto_sipsa, ' + ' ORDER BY producto_sipsa) AS cuales
    FROM puente_producto
    WHERE item_codigo_fao IS NOT NULL
    GROUP BY item_codigo_fao
    HAVING count(*) > 1
    ORDER BY productos_sipsa DESC
    """
)
st.markdown("**Ítems de FAOSTAT que reciben más de un producto de SIPSA**")
st.dataframe(colisiones, width="stretch", hide_index=True)

# --- Limitaciones -----------------------------------------------------------

st.subheader("Limitaciones declaradas")
st.markdown(
    """
1. **La grilla de NASA POWER promedia el relieve.** A Villavicencio, que está a 467 m, le
   asigna 1.392 m. Las temperaturas absolutas no caracterizan la zona; las anomalías sí.
2. **Las coordenadas de zona productora son capitales departamentales**, usadas como
   aproximación. Falta refinarlas con polígonos de producción.
3. **El endpoint mensual de NASA POWER va con más de un año de rezago** y sirve años
   completos, no meses cerrados.
4. **Los últimos trimestres del ONI son provisionales**: se revisan hasta dos meses después.
5. **SIPSA arranca en febrero de 2020** en el servicio web. Para historia más larga hay que
   sumar los microdatos del DANE de 2013 a 2024.
6. **El precio de SIPSA se interpreta como pesos por kilogramo.** La guía del DANE lo describe
   como cantidad, pero los valores solo tienen sentido como precio. Falta validarlo contra un
   boletín publicado.
7. **La API REST de FAOSTAT exige token** y no se pudo verificar su esquema de autenticación.
   La carga histórica no depende de ella: sale de las descargas masivas.
"""
)
