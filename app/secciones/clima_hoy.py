"""Clima hoy: que esta pasando y que se espera en las zonas productoras.

Seccion de la pagina Clima (antes era la pagina "Clima hoy").

Dos horizontes distintos y conviene no confundirlos: el dia a dia (16 dias,
bastante confiable) y el estacional (meses, apenas una tendencia).
"""

import pandas as pd
import streamlit as st

import estilo
import graficas
from datos import (clima_diario, departamentos_clima, fecha, pronostico_estacional,
                   tabla_existe)


def mostrar() -> None:
    """Clima de los ultimos dias y lo que se espera en una zona productora."""
    if not tabla_existe("fact_clima_diario"):
        st.info(
            "Esta página necesita las tablas `fact_clima_diario` y `fact_pronostico_estacional`, "
            "que llegan con la fuente Open-Meteo. Todavía no están en la base: corré "
            "`scripts/actualizar.py` y `scripts/integrar.py`."
        )
        return

    estilo.explicacion(
        "El clima se mide en la <b>zona productora</b>, no en la ciudad donde se vende: la lluvia que "
        "afecta la cosecha cae donde se siembra. Lo <b>observado</b> ya pasó y está medido; el "
        "<b>pronóstico</b> es una estimación y se dibuja punteado o translúcido. "
        "Que llueva distinto no significa que el precio vaya a cambiar: "
        "<b>correlación no es causalidad</b>."
    )

    zonas = departamentos_clima()
    nombres = dict(zip(zonas["dpto_codigo"], zonas["departamento"]))
    codigo = st.selectbox("Zona productora", zonas["dpto_codigo"].tolist(),
                          format_func=lambda c: nombres[c])

    clima = clima_diario(codigo)
    if clima.empty:
        st.info(f"No hay clima descargado para {nombres[codigo]}.")
        return

    observado = clima[clima["tipo"] == "observado"]
    pronostico = clima[clima["tipo"] == "pronostico"]
    ultimo = observado["fecha"].max()
    ultimos_7 = observado[observado["fecha"] > ultimo - pd.Timedelta(days=7)]
    lluvia_7 = float(ultimos_7["precipitacion_mm"].sum())
    lluvia_pronostico = float(pronostico["precipitacion_mm"].sum()) if not pronostico.empty else None

    tarjetas = [
        estilo.tarjeta("Último día medido", ultimo.strftime("%d/%m/%Y"),
                       f"{len(observado)} días en la gráfica"),
        estilo.tarjeta("Llovió en 7 días", f"{lluvia_7:.0f} mm",
                       "suma de la última semana medida (1 mm = 1 litro de agua por metro cuadrado)"),
        estilo.tarjeta("Temperatura máxima", f"{estilo.decimal(ultimos_7['temp_max'].max())} °C",
                       "la más alta de la última semana"),
    ]
    if lluvia_pronostico is not None:
        tarjetas.append(estilo.tarjeta(
            "Lluvia pronosticada", f"{lluvia_pronostico:.0f} mm",
            f"próximos {len(pronostico)} días", color=estilo.AZUL))
    estilo.fila_de_tarjetas(tarjetas)

    st.subheader(f"Día a día en {nombres[codigo]}")
    estilo.grafica(graficas.clima_dia_a_dia(clima))
    st.caption(
        "Barras: lluvia del día (eje izquierdo). Líneas: temperatura máxima y mínima (eje derecho). "
        "Las barras **sólidas** y las líneas continuas son lo medido; las **translúcidas** y "
        "punteadas, el pronóstico. La línea gris vertical marca dónde termina lo medido."
    )

    # --- Pronostico estacional ---------------------------------------------------
    st.subheader("Lluvia esperada en los próximos meses")

    if not tabla_existe("fact_pronostico_estacional"):
        st.info("El pronóstico estacional llega con la tabla `fact_pronostico_estacional`.")
    else:
        estacional = pronostico_estacional(codigo)
        if estacional.empty:
            st.info(f"Todavía no hay pronóstico estacional para {nombres[codigo]}.")
        else:
            estilo.grafica(graficas.lluvia_esperada(estacional))
            st.caption(
                "La línea punteada es la lluvia esperada del mes y la banda azul el rango probable: "
                "**cuanto más ancha la banda, menos de acuerdo están los modelos**. "
                f"Va de {fecha(int(estacional['periodo'].min()))} a "
                f"{fecha(int(estacional['periodo'].max()))}."
            )

            seco = estacional[estacional["anomalia_p50"] < 0]
            humedo = estacional[estacional["anomalia_p50"] > 0]
            frases = []
            if not humedo.empty:
                frases.append("más lluvias que lo habitual en "
                              + ", ".join(fecha(int(p)) for p in humedo["periodo"]))
            if not seco.empty:
                frases.append("menos lluvias que lo habitual en "
                              + ", ".join(fecha(int(p)) for p in seco["periodo"]))
            if frases:
                st.markdown("**Frente a un mes normal:** se esperan " + "; ".join(frases) + ".")
            st.caption(
                "Un mes más seco de lo normal en la zona productora puede adelantar o reducir una "
                "cosecha, y eso **a veces** mueve el precio semanas después. Esta página muestra el "
                "clima; la relación con el precio se analiza en «¿Cuánto afecta el clima?» y no es una predicción."
            )

