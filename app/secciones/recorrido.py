"""Recorrido paso a paso: de seis fuentes desordenadas a una alerta.

Esta pagina es para aprender. Cada paso tiene:
  - una explicacion en palabras simples
  - datos REALES de antes y de despues
  - el pedazo de codigo que lo hace, explicado linea por linea
"""

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import estilo
from datos import con_indicadores, consultar, fecha, puente, ultimo_mes_cerrado
from src.indicators.volatilidad import MINIMO_OBSERVACIONES, UMBRAL_AMARILLA, UMBRAL_ROJA

EJEMPLOS = Path(__file__).resolve().parents[1] / "ejemplos"


def mostrar() -> None:
    """Los cinco pasos, de las seis fuentes a la alerta, con datos reales."""
    # Linea de los cinco pasos, con una animacion que los va mostrando en orden.
    pasos = ["1 · Traer", "2 · Limpiar", "3 · Homologar", "4 · Unir", "5 · Detectar"]
    st.html(
        '<div style="display:flex; flex-wrap:wrap; gap:.4rem; align-items:center; margin:.4rem 0 1rem 0">'
        + '<span style="color:#9A9384">→</span>'.join(
            f'<span class="chip anim anim-{i}" style="font-size:.95rem; padding:.35rem .9rem; '
            f'background:{estilo.VERDE}; color:#fff; border:none">{p}</span>'
            for i, p in enumerate(pasos)
        )
        + "</div>"
    )
    estilo.explicacion(
        "Es como preparar un <b>sancocho</b>. Primero se <b>consiguen</b> los ingredientes en "
        "distintos sitios (adquirir). Luego se <b>lavan y pelan</b> (limpiar). Después se "
        "<b>cortan del mismo tamaño</b> para que se cocinen igual (homologar). Se echan en "
        "<b>la misma olla</b> (integrar). Y al final se <b>prueba</b> para saber si algo "
        "está raro (detectar).",
        etiqueta="La idea en una frase",
    )

    # =============================================================================
    estilo.paso(1, "Traer los datos (adquisición)", "Python: librería requests")
    # =============================================================================
    estilo.explicacion(
        "Cada fuente entrega sus datos de una forma distinta. Algunas tienen una <b>API</b>: una "
        "dirección web a la que un programa le pide datos y recibe una respuesta ordenada. Otras "
        "solo dejan descargar un archivo. Nuestro código en Python hace esas peticiones y guarda "
        "lo que llega <b>sin tocarlo</b> en <code>data/raw/</code>, con la fecha del día."
    )
    st.dataframe(
        pd.DataFrame([
            ("SIPSA · DANE", "API SOAP", "XML", "Diario", "Precio mayorista (COP/kg)"),
            ("IDEAM", "API Socrata", "JSON", "Cada 10 min", "Lluvia medida por un sensor (mm)"),
            ("FAOSTAT", "Descarga masiva", "ZIP con CSV", "Anual", "Producción, comercio, precios"),
            ("NASA POWER", "API REST", "JSON", "Mensual y diaria", "Lluvia y temperatura por zona"),
            ("ONI · NOAA", "Archivo de texto", "TXT", "Mensual", "El Niño / La Niña"),
            ("Pink Sheet", "Descarga", "Excel", "Mensual", "Fertilizantes y energía (USD)"),
        ], columns=["Fuente", "Cómo se pide", "Formato", "Frecuencia", "Qué nos da"]),
        width="stretch", hide_index=True,
    )

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Así llega un precio desde SIPSA** (un registro real del XML):")
        st.code(
            "<return>\n"
            "  <ciudad>MANIZALES</ciudad>\n"
            "  <codProducto>16</codProducto>\n"
            "  <fechaCaptura>2026-09-10T00:00:00-05:00</fechaCaptura>\n"
            "  <precioPromedio>3500</precioPromedio>\n"
            "  <producto>Guayaba*</producto>\n"
            "</return>",
            language="xml",
        )
    with c2:
        st.markdown("**Y así llega una lectura del sensor del IDEAM** (JSON real):")
        st.code(
            '{\n  "codigoestacion": "0021201200",\n  "codigosensor": "0240",\n'
            '  "fechaobservacion": "2026-09-21T23:59:00.000",\n  "valorobservado": "0",\n'
            '  "descripcionsensor": "PRECIPITACIÓN",\n  "unidadmedida": "mm"\n}',
            language="json",
        )

    with st.expander("Ver el código (explicado)"):
        st.code(
            '''import requests                                # librería para hacer peticiones web

url = "https://www.datos.gov.co/resource/s54a-sgyg.json"   # dirección de la API
params = {"$where": "departamento = 'Boyacá'",  # filtro: solo Boyacá
          "$limit": "50000"}                    # máximo de filas por petición

respuesta = requests.get(url, params=params, timeout=180)  # pedimos los datos
respuesta.raise_for_status()                    # si la API responde error, paramos aquí
datos = respuesta.json()                        # convertimos el texto JSON en una lista de Python

# Guardamos tal cual llegó: los datos crudos no se modifican nunca.
open("data/raw/ideam/2026-09-22/precipitacion.json", "w").write(respuesta.text)''',
            language="python",
        )
        st.caption("Versión simplificada. El código completo está en src/acquisition/ (un archivo por fuente).")

    # =============================================================================
    estilo.paso(2, "Limpiar y ordenar", "Python: pandas")
    # =============================================================================
    estilo.explicacion(
        "Los datos crudos traen problemas: fechas con zona horaria, nombres que cambian, "
        "códigos que significan \"no hay dato\" y frecuencias distintas. Limpiar es dejarlos "
        "<b>con el mismo formato</b> y en la <b>misma frecuencia</b>. Aquí todo se lleva a "
        "<b>un dato por mes</b>, porque es la frecuencia que comparten casi todas las fuentes."
    )
    st.markdown("**Problemas reales que encontramos y cómo los resolvimos**")
    st.dataframe(
        pd.DataFrame([
            ("Fecha con zona horaria", "2026-09-10T00:00:00-05:00", "2026-09-10", "Se deja solo la fecha"),
            ("Mercado renombrado", "CÚCUTA (hasta dic. 2022)", "SAN JOSÉ DE CÚCUTA", "Se unifica para no partir la serie"),
            ("Código de \"no hay dato\"", "-999 (NASA POWER)", "vacío", "Si no, contaría como temperatura real"),
            ("Asterisco en el nombre", "Papa negra*", "Papa negra + es_variedad = sí", "El * marca variedad: se guarda aparte"),
            ("Frecuencia diaria", "20 precios en agosto", "1 promedio mensual", "Para cruzar con fuentes mensuales"),
        ], columns=["Problema", "Antes", "Después", "Por qué"]),
        width="stretch", hide_index=True,
    )

    st.markdown("**Ejemplo real: de 20 precios diarios a 1 precio mensual** (papa negra, Bogotá, agosto de 2026)")
    diario = pd.read_csv(EJEMPLOS / "sipsa_diario_papa_bogota_2026_08.csv", parse_dates=["fecha"])
    mensual = consultar(
        "SELECT periodo, precio_cop_kg, precio_min, precio_max, dias_con_dato "
        "FROM fact_precio_mayorista WHERE producto = 'Papa negra*' "
        "AND mercado = 'BOGOTÁ, D.C.' AND periodo = 202608"
    )
    c1, c2 = st.columns([1.4, 1])
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=diario["fecha"], y=diario["precio_cop_kg"], mode="markers+lines",
                                 name="precio de cada día", line=dict(color=estilo.GRIS, width=1),
                                 marker=dict(color=estilo.VERDE, size=8)))
        if not mensual.empty:
            fig.add_hline(y=float(mensual["precio_cop_kg"][0]), line_color=estilo.ROJO, line_dash="dash",
                          annotation_text=f"promedio del mes: {estilo.pesos(mensual['precio_cop_kg'][0])}",
                          annotation_position="top left")
        fig.update_layout(title="Antes: un precio por día", yaxis_tickprefix="$", yaxis_tickformat=",.0f",
                          xaxis_tickformat="%d/%m", height=330, showlegend=False)
        estilo.grafica(fig)
        st.caption("Cada punto verde es el precio de un día (eje vertical); la línea roja punteada es el "
                   "promedio del mes, el único número que guardamos.")
    with c2:
        st.markdown("**Después: una sola fila para todo el mes**")
        if not mensual.empty:
            m = mensual.iloc[0]
            st.dataframe(pd.DataFrame({
                "columna": ["periodo", "precio_cop_kg", "precio_min", "precio_max", "dias_con_dato"],
                "valor": [str(int(m["periodo"])), estilo.pesos(m["precio_cop_kg"]), estilo.pesos(m["precio_min"]),
                          estilo.pesos(m["precio_max"]), str(int(m["dias_con_dato"]))],
                "qué es": ["año y mes (AAAAMM)", "promedio de los días", "precio más bajo del mes",
                           "precio más alto del mes", "cuántos días se promediaron"],
            }), width="stretch", hide_index=True)
        st.caption("dias_con_dato guarda cuántos días se promediaron: un mes con 2 días no vale lo mismo que uno con 20.")

    with st.expander("Ver el código (explicado)"):
        st.code(
            '''mensual = (
    diario.groupby(["mercado", "producto", "anio", "mes"])   # agrupar: una caja por mercado-producto-mes
    .agg(precio_cop_kg=("precio_cop_kg", "mean"),           # promedio de los precios de la caja
         dias_con_dato=("precio_cop_kg", "count"),          # cuántos días había
         precio_min=("precio_cop_kg", "min"),               # el más bajo del mes
         precio_max=("precio_cop_kg", "max"))               # el más alto del mes
    .reset_index()                                          # volver a tabla normal
)''',
            language="python",
        )
        st.caption("Código real en src/cleaning/sipsa.py, función a_mensual.")

    # =============================================================================
    estilo.paso(3, "Homologar: que todos hablen el mismo idioma", "OpenRefine + tabla de correspondencias")
    # =============================================================================
    estilo.explicacion(
        "SIPSA dice <b>\"Papa negra*\"</b>. La FAO dice <b>\"Potatoes\"</b>, con código 116. Son "
        "la misma cosa con nombres distintos, y el computador no lo sabe. <b>Homologar</b> es "
        "armar una tabla que diga qué producto de una fuente corresponde a cuál de la otra, y "
        "<b>qué tan exacta</b> es esa correspondencia."
    )
    p = puente()
    conteo = p["tipo_correspondencia"].value_counts()
    significado = {
        "exacta": "El mismo producto en las dos fuentes. Se pueden comparar precios.",
        "agregada": "La FAO junta varios productos en un código (limón común + limón Tahití).",
        "generica": "Cae en un cajón de \"otros\" de la FAO (\"Other tropical fruits\").",
        "sin_equivalente": "La FAO no lo publica para Colombia.",
    }
    estilo.fila_de_tarjetas([
        estilo.tarjeta({"exacta": "Exacta", "agregada": "Agregada", "generica": "Genérica",
                        "sin_equivalente": "Sin equivalente"}[tipo], f"{int(conteo.get(tipo, 0))} de {len(p)}", texto,
                       color=[estilo.VERDE, estilo.AMARILLO, estilo.TIERRA, estilo.ROJO][i], retraso=i)
        for i, (tipo, texto) in enumerate(significado.items())
    ], ancho_minimo=230)
    st.dataframe(
        p[["producto_sipsa", "item_codigo_fao", "item_fao", "tipo_correspondencia"]].rename(columns={
            "producto_sipsa": "Nombre en SIPSA", "item_codigo_fao": "Código FAO",
            "item_fao": "Nombre en FAO", "tipo_correspondencia": "Tipo"}),
        width="stretch", hide_index=True, height=260,
    )
    st.caption("La tabla vive en config/homologacion_productos.csv. OpenRefine se usó para revisar y agrupar los nombres (receta en data/openrefine/).")

    # =============================================================================
    estilo.paso(4, "Unir todo en una sola tabla (integración)", "DuckDB (SQL) · Power Query en Excel")
    # =============================================================================
    estilo.explicacion(
        "Para unir dos tablas se necesita una columna que tengan en común: la <b>variable de "
        "integración</b>. Es como el número de cédula: con él se encuentra a la misma persona "
        "en dos bases distintas. Aquí usamos tres: <b>año y mes</b>, <b>departamento</b> y "
        "<b>producto</b> (este último a través de la tabla del paso 3)."
    )
    estilo.fila_de_tarjetas([
        estilo.tarjeta("Año + mes", "periodo", "Une las 6 fuentes en el tiempo", color=estilo.AZUL, retraso=0),
        estilo.tarjeta("Departamento", "Cundinamarca", "Une precio con clima de su zona productora",
                       color=estilo.VERDE, retraso=1),
        estilo.tarjeta("Producto", "Papa negra* ↔ 116", "Une SIPSA con FAOSTAT", color=estilo.AMARILLO, retraso=2),
    ], ancho_minimo=240)

    sql = """SELECT p.anio, p.mes,
       p.precio_cop_kg              AS precio_papa_bogota,
       c.precipitacion_anomalia     AS lluvia_vs_normal_mm_dia,
       e.anomalia                   AS oni_el_nino
FROM fact_precio_mayorista p
JOIN puente_zona_sipsa z  ON z.producto_sipsa = p.producto        -- producto -> zona productora
LEFT JOIN fact_clima c    ON c.departamento = z.departamento      -- zona -> clima (NASA POWER)
                         AND c.producto = z.producto_zona
                         AND c.anio = p.anio AND c.mes = p.mes    -- mismo año y mes
LEFT JOIN fact_enso e     ON e.anio = p.anio AND e.mes = p.mes    -- mismo año y mes -> El Niño
WHERE p.producto = 'Papa negra*' AND p.mercado = 'BOGOTÁ, D.C.'
  AND z.departamento = 'Cundinamarca'
ORDER BY p.anio, p.mes"""
    st.code(sql, language="sql")
    unida = consultar(sql)
    st.markdown("**Resultado: precio, clima y El Niño en la misma fila** (últimos 12 meses)")
    st.dataframe(
        unida.tail(12),
        column_config={
            "anio": st.column_config.NumberColumn("año", format="%d"),
            "precio_papa_bogota": st.column_config.NumberColumn("precio papa Bogotá (COP/kg)", format="$%.0f"),
            "lluvia_vs_normal_mm_dia": st.column_config.NumberColumn("lluvia vs normal (mm/día)", format="%.2f"),
            "oni_el_nino": st.column_config.NumberColumn("ONI (°C)", format="%+.2f"),
        },
        width="stretch", hide_index=True,
    )
    st.caption(
        "El endpoint mensual de NASA POWER publica con meses de rezago; los meses más recientes se "
        "completan con su endpoint diario (columna fuente = diario en fact_clima). El sensor del IDEAM "
        "llega casi en tiempo real."
    )

    # =============================================================================
    estilo.paso(5, "Detectar lo raro (la alerta)", "Python: pandas + numpy")
    # =============================================================================
    estilo.explicacion(
        "No basta con ver si el precio subió: la papa sube y baja todo el tiempo. La pregunta es "
        "<b>¿este cambio es raro para este producto en este mercado?</b> Para eso se compara el "
        "cambio del mes con todos los cambios anteriores de esa misma serie."
    )
    st.latex(r"r_t = \ln\left(\frac{P_t}{P_{t-1}}\right) \qquad z_t = \frac{r_t - \bar{r}}{s}")
    st.markdown(
        f"- **r** es el *retorno logarítmico*: cuánto cambió el precio. Se usa logaritmo porque "
        f"subir 50 % y luego bajar 33 % te deja igual, y el logaritmo lo refleja: +0,405 − 0,405 = 0.\n"
        f"- **r̄** y **s** son el promedio y la desviación estándar de los cambios de esa serie, "
        f"usando **solo meses pasados** (mínimo {MINIMO_OBSERVACIONES}), como si estuviéramos en ese mes.\n"
        f"- **z** dice a cuántas desviaciones quedó el cambio de lo normal: más de "
        f"{UMBRAL_AMARILLA:g} → amarilla, más de {UMBRAL_ROJA:g} → roja."
    )

    # Ejemplo trabajado con la alerta mas fuerte del ultimo mes cerrado.
    df = con_indicadores()
    mes = ultimo_mes_cerrado()
    alertas_mes = df[(df["periodo"] == mes) & df["alerta"].isin(["roja", "amarilla"])]
    if not alertas_mes.empty:
        fila = alertas_mes.loc[alertas_mes["z_score"].abs().idxmax()]
        serie = df[(df["producto"] == fila["producto"]) & (df["mercado"] == fila["mercado"])].sort_values("periodo")
        hasta = serie[serie["periodo"] <= mes]["retorno_log"].dropna()
        previo = serie[serie["periodo"] < mes].iloc[-1]
        media, desv = hasta.mean(), hasta.std()
        st.markdown(f"**Ejemplo real:** {fila['producto'].replace('*', '')} en {fila['mercado'].title()}, {fecha(mes)}")
        estilo.fila_de_tarjetas([
            estilo.tarjeta("Precio mes anterior", estilo.pesos(previo["precio_cop_kg"]), fecha(int(previo["periodo"])), retraso=0),
            estilo.tarjeta("Precio este mes", estilo.pesos(fila["precio_cop_kg"]), fecha(mes), retraso=1),
            estilo.tarjeta("Cambio (r)", f"{fila['retorno_log']:+.3f}", f"= ln({fila['precio_cop_kg']:.0f} / {previo['precio_cop_kg']:.0f})", retraso=2),
            estilo.tarjeta("Lo normal (r̄ ± s)", f"{media:+.3f} ± {desv:.3f}", f"{len(hasta)} meses de historia", retraso=3),
            estilo.tarjeta("z", f"{fila['z_score']:+.2f}", f"alerta {fila['alerta']}",
                           color=estilo.COLOR_ALERTA[str(fila['alerta'])], late=True, retraso=4),
        ], ancho_minimo=165)

    with st.expander("Ver el código (explicado)"):
        st.code(
            '''serie["retorno"] = np.log(serie["precio"] / serie["precio"].shift(1))  # cambio vs mes anterior

# expanding(): usa todos los meses desde el inicio HASTA el mes actual, nunca los futuros.
media = serie["retorno"].expanding(min_periods=6).mean()
desv  = serie["retorno"].expanding(min_periods=6).std()

serie["z"] = (serie["retorno"] - media) / desv          # a cuántas desviaciones quedó

serie["alerta"] = pd.cut(serie["z"].abs(),               # clasificar según el tamaño de z
                         bins=[0, 2, 3, np.inf],
                         labels=["verde", "amarilla", "roja"])''',
            language="python",
        )
        st.caption("Código real en src/indicators/volatilidad.py, funciones retornos, volatilidad y alertas.")

    # =============================================================================
    st.subheader("¿Dónde queda guardado todo?")
    estilo.explicacion(
        "En un solo archivo de <b>DuckDB</b> (data/processed/caso8.duckdb), organizado como "
        "<b>modelo estrella</b>: en el centro, tablas de <i>hechos</i> (precios, clima, comercio) y "
        "alrededor, tablas de <i>dimensiones</i> que describen el tiempo, los mercados y los "
        "productos. Esta app solo lee de ese archivo.",
        etiqueta="Modelo estrella",
    )
    tablas = consultar(
        "SELECT table_name AS tabla, estimated_size AS filas FROM duckdb_tables() "
        "WHERE table_name <> 'meta_actualizacion' ORDER BY table_name"
    )
    tablas["tipo"] = np.where(tablas["tabla"].str.startswith("fact_"), "hecho",
                              np.where(tablas["tabla"].str.startswith("dim_"), "dimensión", "puente"))
    st.dataframe(tablas[["tipo", "tabla", "filas"]].sort_values(["tipo", "tabla"]),
                 width="stretch", hide_index=True)
