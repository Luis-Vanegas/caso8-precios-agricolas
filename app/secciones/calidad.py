"""Calidad de datos: lo que encontramos al revisar las fuentes, dicho sin adornos."""

import plotly.graph_objects as go
import streamlit as st

import estilo
from datos import consultar, frescura, puente


def mostrar() -> None:
    """Lo que encontramos al revisar las fuentes y las limitaciones declaradas."""
    # --- Hueco de SIPSA ------------------------------------------------------------------
    st.subheader("¿Qué meses tienen datos de precios?")
    meses = consultar("""
    SELECT CAST(anio || '-' || lpad(CAST(mes AS VARCHAR), 2, '0') || '-01' AS DATE) AS fecha,
           count(*) AS series, median(dias_con_dato) AS dias
    FROM fact_precio_mayorista GROUP BY ALL ORDER BY fecha
""")
    fig = go.Figure(go.Bar(x=meses["fecha"], y=meses["series"], marker_color=estilo.VERDE,
                           customdata=meses["dias"],
                           hovertemplate="%{x|%b %Y}: %{y} series · mediana %{customdata} días<extra></extra>"))
    fig.add_vrect(x0="2020-12-20", x1="2022-01-31", fillcolor=estilo.ROJO, opacity=0.08, line_width=0,
                  annotation_text="sin datos: ene 2021 – ene 2022", annotation_position="top left")
    fig.update_layout(title="Series con precio en cada mes (SIPSA)", height=340)
    estilo.grafica(fig)
    estilo.explicacion(
        "Cada barra es un mes y su altura es cuántas series (un producto en un mercado) tienen precio "
        "ese mes; la franja roja marca el hueco. "
        "El servicio web de SIPSA no entrega <b>ningún precio entre enero de 2021 y enero de 2022</b> "
        "(13 meses). No lo rellenamos: inventar 13 meses de precios sería peor que dejarlos vacíos. "
        "Lo que sí hicimos fue no calcular cambios entre diciembre de 2020 y febrero de 2022, "
        "porque parecería un solo mes y daría alertas falsas."
    )

    # --- Hallazgos ------------------------------------------------------------------------
    st.subheader("Lo que encontramos revisando")
    hallazgos = [
        ("Mercado renombrado", "CÚCUTA → SAN JOSÉ DE CÚCUTA",
         "El DANE cambió el nombre en dic. 2022 y la serie quedaba partida. Se unificó.", estilo.AMARILLO),
        ("Mes en curso", "Datos parciales",
         "El último mes tiene menos días; se marca y no se usa en la portada.", estilo.AMARILLO),
        ("Comercio imposible", "2.730 → 9 casos",
         "Casi todo eran agregados como \"Fruit\" que no se producen. Quedaron 9 inconsistencias reales.", estilo.VERDE),
        ("Unidad de SIPSA", "COP por kg",
         "La guía del DANE dice cantidad; confirmamos que es precio cruzando con FAOSTAT (papa 2,4 %, tomate 0,2 %).", estilo.VERDE),
        ("Precio mayorista vs productor", "No es margen",
         "Coinciden en menos de 3 %: salen del mismo sistema del DANE. Sirven para validar, no para medir intermediación.", estilo.AZUL),
        ("Grilla de NASA POWER", "Relieve promediado",
         "A Villavicencio (467 m) le asigna 1.392 m. Por eso usamos anomalías, no valores absolutos.", estilo.AZUL),
    ]
    estilo.fila_de_tarjetas(
        [estilo.tarjeta(t, d, n, color=c, retraso=i % 4) for i, (t, d, n, c) in enumerate(hallazgos)],
        ancho_minimo=300,
    )

    # --- Homologacion -----------------------------------------------------------------
    st.subheader("Productos que la FAO mezcla en un solo código")
    colisiones = consultar("""
    SELECT item_codigo_fao AS "código FAO", any_value(item_fao) AS "nombre FAO",
           count(*) AS "productos SIPSA", string_agg(producto_sipsa, ' + ' ORDER BY producto_sipsa) AS cuáles
    FROM puente_producto WHERE item_codigo_fao IS NOT NULL
    GROUP BY item_codigo_fao HAVING count(*) > 1 ORDER BY 3 DESC
""")
    st.dataframe(colisiones, width="stretch", hide_index=True)
    st.caption("Para estos productos, el precio al productor de la FAO es una mezcla y no se compara con SIPSA.")

    # --- Frescura y calendario -----------------------------------------------------
    st.subheader("¿Qué tan frescos están los datos?")
    st.dataframe(frescura(), width="stretch", hide_index=True)
    with st.expander("Calendario de publicación de cada fuente"):
        st.markdown("""
| Fuente | Frecuencia | Cuándo publica |
|---|---|---|
| SIPSA mayoristas | Diaria | Días hábiles |
| IDEAM (sensores) | Cada 10 minutos | Casi en tiempo real |
| ONI (NOAA) | Mensual | Los últimos trimestres se revisan hasta 2 meses después |
| Pink Sheet | Mensual | Inicio de mes |
| NASA POWER | Mensual (+ diario para los últimos meses) | El mensual publica con meses de rezago; el diario, con 3 o 4 días |
| FAOSTAT | Anual | Con un año de rezago |
""")

    # --- Limitaciones ---------------------------------------------------------------
    st.subheader("Limitaciones que declaramos")
    st.markdown("""
1. **Sin datos de SIPSA de ene. 2021 a ene. 2022.** Para una historia más larga habría que sumar los microdatos del DANE.
2. **Las zonas productoras son capitales departamentales**, usadas como aproximación; faltan los polígonos de producción (UPRA/EVA).
3. **Solo 13 de 33 productos** tienen correspondencia exacta con la FAO.
4. **La API de FAOSTAT exige token** y no se pudo verificar; la carga histórica sale de las descargas masivas.
5. **Las alertas no se han validado** contra crisis de abastecimiento conocidas: detectan movimientos raros, no predicen crisis.
""")
