"""Sensor IDEAM: de una gota de lluvia a una fila en la base.

Es la fuente de tipo SENSOR del proyecto. La pagina explica la cadena de
adquisicion (DAQ), muestra donde estan las estaciones, como llega un dato crudo
y como lo agregamos. Todo lo numerico sale de la base; los ejemplos de dato
crudo son copias reales guardadas en app/ejemplos/ (la app no depende de la
carpeta de entrega).
"""

import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import estilo
from datos import consultar, fecha, mercados_geo, tabla_existe

EJEMPLOS = Path(__file__).resolve().parents[1] / "ejemplos"


def mostrar() -> None:
    """La fuente de tipo sensor: de una gota de lluvia a una fila en la base."""
    # Si la fuente aun no se cargo, la pagina lo dice y no sigue (no hay nada que mostrar).
    if not tabla_existe("fact_sensor_ideam") or not tabla_existe("dim_estacion_ideam"):
        st.info(
            "Todavía no se ha cargado. Correr en orden: `scripts/actualizar.py --solo ideam`, "
            "`scripts/preparar.py` y `scripts/integrar.py`."
        )
        return

    # --- 1. Cadena de adquisicion (DAQ) -----------------------------------------------------
    # DAQ = Data AcQuisition: los pasos por los que pasa una magnitud fisica hasta ser un dato.
    st.subheader("La cadena de adquisición, paso a paso")
    estilo.fila_de_tarjetas([
        estilo.tarjeta("1 · Fenómeno", "Lluvia",
                       "Agua que cae sobre la estación. Lo que queremos medir: milímetros de lámina de agua.", retraso=0),
        estilo.tarjeta("2 · Transductor", "Balancín",
                       "Pluviómetro de balancín: cada 0,1 mm de lluvia llena una cubeta, el balancín vuelca y un imán "
                       "cierra un interruptor (reed switch). Un vuelco = un pulso eléctrico.", retraso=1),
        estilo.tarjeta("3 · Conteo", "Pulsos",
                       "Un contador suma los pulsos del periodo. Cada pulso vale 0,1 mm, así que "
                       "mm = pulsos × 0,1.", retraso=2),
        estilo.tarjeta("4 · Digitalización", "11 bits",
                       "Rango 0–200 mm con paso de 0,1 mm = 2.000 niveles. Con 10 bits caben 1.024 (no alcanza); "
                       "con 11 caben 2.048 (sí).", retraso=3),
        estilo.tarjeta("5 · Registro", "10 min",
                       "La estación guarda un valor cada 10 minutos (sensor convencional 0240: intervalo mediano "
                       "medido, 10 min).", retraso=4),
        estilo.tarjeta("6 · Transmisión", "GPRS / manual",
                       "Las estaciones con GPRS (sensor 0257) reportan cada ~2 min por red celular; las "
                       "convencionales, cada 10 min.", retraso=1),
        estilo.tarjeta("7 · Publicación", "datos.gov.co",
                       "El IDEAM la publica por API Socrata: dataset s54a-sgyg, unos 165 millones de filas (116 millones con valor).", retraso=2),
        estilo.tarjeta("8 · Nuestro pipeline", "SoQL → DuckDB",
                       "Pedimos al servidor que sume la lluvia por estación y mes (SoQL), limpiamos y "
                       "guardamos en DuckDB.", retraso=3),
    ], ancho_minimo=250)
    estilo.explicacion(
        "<b>Los pasos 2 a 4 son una referencia de diseño, no el equipo confirmado del IDEAM.</b> "
        "Usamos el pluviómetro de balancín (por ejemplo, el Texas Electronics TE525MM, de 0,1 mm por "
        "vuelco) como modelo para explicar cómo se digitaliza la lluvia. Lo que sí está verificado "
        "contra la fuente real es del paso 5 en adelante: el dataset, sus columnas, los códigos de "
        "sensor 0240 y 0257 y sus frecuencias.<br><br>"
        "<b>La cuenta de los bits:</b> 200 mm ÷ 0,1 mm = 2.000 intervalos (2.001 valores si se cuenta "
        "el 0). Con <i>n</i> bits se distinguen 2<sup><i>n</i></sup> valores: 2<sup>10</sup> = 1.024 no "
        "alcanza y 2<sup>11</sup> = 2.048 sí. Por eso 11 bits.",
        etiqueta="Qué es referencia y qué está verificado",
    )

    # --- 2. Contadores reales desde la base ----------------------------------------------------
    resumen = consultar("""
    SELECT count(DISTINCT departamento) AS departamentos,
           count(DISTINCT periodo) AS meses,
           min(periodo) AS primero, max(periodo) AS ultimo
    FROM fact_sensor_ideam
""").iloc[0]
    n_estaciones = int(consultar("SELECT count(*) AS n FROM dim_estacion_ideam")["n"][0])
    st.subheader("Lo que tenemos cargado")
    estilo.contadores([
        ("estaciones con lluvia válida", n_estaciones, "", estilo.AZUL),
        ("departamentos", int(resumen["departamentos"]), "", estilo.VERDE),
        ("meses con dato", int(resumen["meses"]), "", estilo.TIERRA),
    ])
    st.caption(
        f"Periodo cubierto: {fecha(int(resumen['primero']))} a {fecha(int(resumen['ultimo']))}. "
        "Mediana de las estaciones válidas de cada departamento. Los últimos meses pueden estar incompletos."
    )

    # --- 3. Mapa de estaciones (sin internet: solo trazos de paises, sin teselas) ---------------
    st.subheader("Dónde se mide la lluvia y dónde se vende")
    est = consultar("SELECT * FROM dim_estacion_ideam")
    est["proporcion"] = (est["proporcion_meses_validos"] * 100).round(0).astype(int)
    est["municipio"] = est["municipio"].str.title()
    est["nombre"] = est["nombre"].str.title()

    # Ocho departamentos, ocho colores: la paleta de la app tiene seis, se completan dos.
    paleta = estilo.SERIES + ["#7A3E8C", "#2A9D8F"]
    mapa = px.scatter_geo(
        est, lat="lat", lon="lon", color="departamento", color_discrete_sequence=paleta,
        custom_data=["nombre", "municipio", "codigoestacion", "proporcion"],
    )
    mapa.update_traces(
        marker=dict(size=6, opacity=0.8),
        hovertemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} · código %{customdata[2]}<br>"
                      "Meses válidos: %{customdata[3]} %<extra></extra>",
    )
    mercados = mercados_geo()
    mapa.add_trace(go.Scattergeo(
        lat=mercados["lat"], lon=mercados["lon"], mode="markers+text", name="mercados mayoristas",
        text=mercados["mercado"].str.title(), textposition="top right", textfont=dict(size=10, color=estilo.TINTA),
        marker=dict(symbol="square", size=9, color=estilo.TINTA, line=dict(color="#fff", width=1)),
        hovertemplate="<b>Mercado %{text}</b><extra></extra>",
    ))
    mapa.update_geos(
        lataxis_range=[-4.3, 12.8], lonaxis_range=[-79.6, -66.8], resolution=50,
        showcountries=True, countrycolor="#B9B2A0", showland=True, landcolor="#F1ECDF",
        showocean=True, oceancolor="#E8F0F4", showcoastlines=True, coastlinecolor="#B9B2A0",
        bgcolor="rgba(0,0,0,0)",
    )
    mapa.update_layout(title="Estaciones del IDEAM y mercados", height=620, legend=dict(title=None, y=0.02, x=0.01),
                       margin=dict(l=0, r=0, t=50, b=0))
    estilo.grafica(mapa)
    estilo.explicacion(
        "Cada <b>punto de color</b> es una estación de lluvia, y el color es su departamento. Cada "
        "<b>cuadrado oscuro</b> es una plaza mayorista cuyos precios analizamos. Pasá el mouse sobre un "
        "punto para ver su nombre, municipio, código y en qué porcentaje de los meses su dato salió "
        "válido. Se ve que hay lluvia medida cerca de varios mercados, pero no de todos: hay mercados "
        "(la costa, por ejemplo) sin ninguna estación en nuestras zonas productoras, porque solo bajamos "
        "los 8 departamentos productores.",
        etiqueta="Cómo leerlo",
    )

    # --- 4. Asi llega un dato del sensor --------------------------------------------------------
    st.subheader("Así llega un dato del sensor")
    crudo_texto = (EJEMPLOS / "ideam_lectura_cruda_sensor.json").read_text(encoding="utf-8")
    agregado_texto = (EJEMPLOS / "ideam_agregado_estacion_mes.json").read_text(encoding="utf-8")
    agregado = json.loads(agregado_texto)[0]
    tolima = consultar(
        "SELECT * FROM fact_sensor_ideam WHERE departamento = 'Tolima' AND periodo = 202607"
    )
    izq, der = st.columns(2, gap="large")
    with izq:
        st.markdown("**1. Lectura cruda** (dos lecturas reales de la API)")
        st.code(crudo_texto, language="json")
        st.markdown(
            "- `codigoestacion` y `codigosensor`: qué estación y qué sensor. `0240` es convencional y `0257` GPRS.\n"
            "- `fechaobservacion`: el minuto de la lectura.\n"
            "- `valorobservado`: la lluvia en `unidadmedida` (mm) en ese intervalo. Aquí `0`: no llovió.\n"
            "- Los demás campos ubican la estación (nombre, departamento, municipio, coordenadas)."
        )
    with der:
        st.markdown("**2. Agregado mensual por estación** (lo que pide nuestra consulta SoQL)")
        st.code(agregado_texto, language="json")
        st.markdown(
            f"- `suma`: la lluvia del mes en mm (**{float(agregado['suma']):.1f} mm**). Es el valor físico que usamos.\n"
            f"- `n_lecturas`: cuántas lecturas entraron ({int(agregado['n_lecturas']):,}".replace(",", ".") +
            "). Sirve para saber si el mes está completo.\n"
            "- `minimo` y `maximo`: la lectura más baja y la más alta; si el mínimo fuera negativo, la estación fallaría.\n"
            "- `promedio`: no se usa para la lluvia (se acumula, no se promedia)."
        )
    if not tolima.empty:
        f = tolima.iloc[0]
        st.markdown("**3. Fila ya agregada por departamento** (`fact_sensor_ideam`, julio 2026, Tolima)")
        st.dataframe(tolima, hide_index=True, width="stretch")
        st.markdown(
            f"- `valor`: **{f['valor']:.2f} mm**, la *mediana* de la lluvia del mes entre las "
            f"{int(f['n_estaciones'])} estaciones válidas del Tolima (la mediana evita que una estación "
            "descalibrada arrastre el dato).\n"
            f"- `anomalia`: {f['anomalia']:+.1f} mm frente al promedio de los meses de julio de ese departamento.\n"
            "- `periodo`: AAAAMM, la llave para cruzar con precios y clima."
        )
    estilo.explicacion(
        "Lo crudo (millones de lecturas de 10 minutos) nunca baja completo: pedimos que el servidor sume "
        "por estación y mes, y nosotros resumimos por departamento. La estación de la columna 2 "
        "(Cajamarca, Tolima) es una de las que entra en la mediana de la fila 3. Las dos lecturas "
        "crudas de la columna 1 son de otras estaciones, solo para mostrar el formato.",
    )

    # --- 5. Grafica mensual por departamento -----------------------------------------------------
    st.subheader("La lluvia mes a mes")
    s = consultar("SELECT * FROM fact_sensor_ideam WHERE variable = 'precipitacion' ORDER BY anio, mes")
    depto = st.selectbox("Departamento", sorted(s["departamento"].unique()))
    d = s[s["departamento"] == depto].copy()
    d["fecha"] = pd.to_datetime(dict(year=d["anio"], month=d["mes"], day=1))
    fig = go.Figure(go.Bar(
        x=d["fecha"], y=d["anomalia"],
        marker_color=[estilo.AZUL if v > 0 else estilo.TIERRA for v in d["anomalia"]],
        customdata=d[["valor", "n_estaciones"]],
        hovertemplate="%{x|%b %Y}: %{customdata[0]:.0f} mm en el mes "
                      "(%{customdata[1]} estaciones)<br>vs normal: %{y:+.0f} mm<extra></extra>"))
    fig.update_layout(title="Lluvia del mes vs lo normal (mm)", height=340)
    estilo.grafica(fig)
    st.caption(f"Departamento: {depto}.")
    estilo.explicacion(
        "Cada barra es un mes. Su altura es cuántos milímetros llovió <b>de más (azul)</b> o <b>de "
        "menos (café)</b> que el promedio de ese mismo mes del año en ese departamento. Pasá el mouse "
        "para ver la lluvia total del mes y cuántas estaciones la midieron. Los meses con pocas "
        "estaciones (los más recientes) son menos confiables.",
        etiqueta="Cómo leerlo",
    )

    # --- 6. Limitaciones honestas ----------------------------------------------------------------
    st.subheader("Qué no hace (todavía)")
    st.markdown(
        "- **Solo lluvia.** La temperatura del aire (dataset `sbwg-7ju4`) está verificada contra la API, "
        "pero no se descargó; la app no la muestra.\n"
        "- **Hubo huecos y se resolvieron.** Cundinamarca no había bajado dic-2024 ni ene-2025 (la API daba "
        "timeout incluso pidiendo un mes) y Antioquia no tenía ningún archivo. Se resolvió pidiendo "
        "ventanas de 5 días y combinándolas (las sumas y los conteos se suman; el mínimo y el máximo se "
        "recalculan). Antioquia se bajó con el mismo método.\n"
        "- **Hay meses sin dato** (por ejemplo, Meta tiene 69 de 81 meses entre ene 2020 y sep 2026): "
        "son huecos reales y se declaran, no se rellenan.\n"
        "- **Los sensores GPRS y convencional no se suman.** Una estación puede tener ambos; mezclarlos "
        "contaría la lluvia dos veces, por eso se agrupa también por código de sensor.\n"
        "- **El modelo del sensor es una referencia de diseño**, no el equipo confirmado del IDEAM.\n"
        "- **Quindío llega a julio de 2026**; los demás departamentos, a septiembre."
    )

    # --- 7. Fuentes --------------------------------------------------------------------------------
    st.subheader("Fuentes")
    st.markdown(
        "- [IDEAM, *Precipitación*, dataset s54a-sgyg, Datos Abiertos Colombia](https://www.datos.gov.co/d/s54a-sgyg) "
        "(API Socrata; fuente de los datos).\n"
        "- [Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM)](https://www.ideam.gov.co/).\n"
        "- WMO, *Guide to Instruments and Methods of Observation*, WMO-No. 8 (2023), vol. I, cap. 6 y anexo 1.A "
        "(Organización Meteorológica Mundial). Referencia de resolución y rango de la lluvia; "
        "falta contrastar las cifras con el texto.\n"
        "- [Texas Electronics, pluviómetros de balancín](https://texaselectronics.com/tipping-bucket-rain-gauges/): "
        "fabricante del TE525MM. **Solo referencia de diseño**, no es el modelo confirmado del IDEAM; "
        "la ficha del TE525MM no se pudo comprobar en la página, hay que leerla en su hoja técnica."
    )
