"""La cadena: lluvia en la zona productora -> toneladas que llegan -> precio.

Las tres series en el mismo eje de tiempo para poder leerlas en vertical. NO
afirma que una cause la otra: solo las pone juntas. Antes era la pagina "La
cadena"; ahora es una pestana de "¿Cuanto afecta el clima?".
"""

import streamlit as st

import estilo
import graficas
from datos import (UMBRAL_Q, articulos_cadena, cadena, departamentos_cadena, fecha,
                   fuente_precio, mercados_diarios, par_diario, sensibilidad_cadena,
                   tabla_existe)


def mostrar() -> None:
    """Lluvia, toneladas y precio de un articulo en un departamento, mes a mes."""
    if not (tabla_existe("fact_abastecimiento") and tabla_existe("fact_clima_diario")):
        st.info(
            "Esta página necesita `fact_abastecimiento`, `fact_clima_diario` y "
            "`fact_precio_semanal`. Alguna todavía no está en la base."
        )
        return

    estilo.explicacion(
        "Leé la gráfica <b>en vertical</b>: buscá un mes con mucha o poca lluvia y mirá qué pasó "
        "debajo, en las toneladas y en el precio, ese mes y los siguientes. El efecto del clima "
        "tarda: entre la lluvia y la góndola pasan semanas o meses. "
        "Que dos series se muevan parecido <b>no demuestra</b> que una cause la otra: "
        "<b>correlación no es causalidad</b>. La medición formal está en la pestaña "
        "«Lo que encontramos»."
    )

    st.caption(
        "**Una aclaración necesaria:** la lluvia que se muestra es la del **mismo departamento de la "
        "central**, que no siempre es donde se cultivó lo que llegó a esa central. La papa que se "
        "vende en Bogotá puede venir de Boyacá o de Nariño. El proyecto todavía no tiene la "
        "trazabilidad origen → destino de cada carga, así que esta gráfica compara el clima local, "
        "y eso limita lo que se puede concluir."
    )

    articulos = articulos_cadena()

    if articulos.empty:
        st.info("Todavía no hay artículos con abastecimiento y precio a la vez.")
        return

    izq, der = st.columns(2, gap="large")
    with izq:
        opciones = articulos["art_id"].tolist()
        etiquetas = dict(zip(articulos["art_id"], articulos["articulo"]))
        art_id = st.selectbox("Artículo", opciones, format_func=lambda a: etiquetas[a])

    zonas = departamentos_cadena(art_id)
    if zonas.empty:
        st.info(f"**{etiquetas[art_id]}** no tiene abastecimiento en ningún departamento con clima "
                "descargado. Probá otro artículo.")
        return

    with der:
        nombres = dict(zip(zonas["dpto_codigo"], zonas["departamento"]))
        codigo = st.selectbox("Departamento", zonas["dpto_codigo"].tolist(),
                              format_func=lambda c: nombres[c])

    # De donde sale el precio: el diario (desde 2020) si el articulo tiene par
    # exacto y el departamento tiene mercado diario; si no, el semanal (13 meses).
    producto_diario = fuente_precio(art_id, codigo)
    df = cadena(art_id, codigo, producto_diario)
    if df.empty:
        st.info(f"No hay datos de **{etiquetas[art_id]}** en {nombres[codigo]}.")
        return

    # Los meses donde las tres series existen a la vez: es el unico tramo donde la
    # cadena completa se puede leer, y conviene decirlo antes de mostrarla.
    completos = df.dropna(subset=["lluvia_mm", "toneladas", "precio"])
    unidad = df["unidad"].dropna().iloc[0] if df["unidad"].notna().any() else "kg"

    if producto_diario:
        mercados = ", ".join(m.split(",")[0].title() for m in mercados_diarios(codigo))
        st.info(
            f"**Fuente del precio: precio diario de SIPSA, promedio mensual, desde 2020** "
            f"(producto «{producto_diario.replace('*', '')}», mercado de {mercados}). "
            "Este artículo tiene el mismo nombre en el abastecimiento y en el precio diario, así que "
            "se puede usar la serie larga. Con ella la cadena se cruza en muchos más meses que con "
            "el precio semanal."
        )
    else:
        motivo = ("no tiene un artículo con el mismo nombre en el precio diario"
                  if par_diario(art_id) is None
                  else f"{nombres[codigo]} no tiene mercado en el precio diario")
        st.info(
            f"**Fuente del precio: precio semanal de SIPSA** (solo los últimos doce meses, aprox.). "
            f"No se usa el precio diario, que llega a 2020, porque {motivo}. Emparejar nombres "
            "distintos mezclaría variedades (por ejemplo, «Papa negra» agrupa varias papas)."
        )

    estilo.fila_de_tarjetas([
        estilo.tarjeta("Meses con lluvia", f"{int(df['lluvia_mm'].notna().sum())}", "clima observado"),
        estilo.tarjeta("Meses con toneladas", f"{int(df['toneladas'].notna().sum())}", "abastecimiento"),
        estilo.tarjeta("Meses con precio", f"{int(df['precio'].notna().sum())}",
                       "precio diario (mensual)" if producto_diario else "precios semanales"),
        estilo.tarjeta("Las tres a la vez", f"{len(completos)}",
                       f"{fecha(int(completos['periodo'].min()))} a {fecha(int(completos['periodo'].max()))}"
                       if not completos.empty else "ningún mes en común",
                       color=estilo.VERDE if len(completos) >= 12 else estilo.AMARILLO),
    ])

    if completos.empty:
        st.warning(
            "Para esta combinación no hay ningún mes con las tres series a la vez, así que la cadena "
            "no se puede leer completa. Probá otro artículo o departamento."
        )
    elif len(completos) < 12:
        st.warning(
            f"**Las tres series coinciden en solo {len(completos)} meses.** "
            + ("Los precios semanales del DANE son una ventana móvil de doce meses y el "
               "abastecimiento va unos meses atrasado, así que el tramo comparable es corto. "
               if not producto_diario else "")
            + "Alcanza para mirar, no para concluir."
        )

    st.subheader(f"{etiquetas[art_id]} · {nombres[codigo]}")
    estilo.grafica(graficas.cadena_lluvia_oferta_precio(df, unidad))
    st.caption(
        "Arriba la lluvia del mes en la zona productora; en el medio las toneladas que entraron a la "
        "central; abajo el precio. Las líneas **se cortan donde no hay dato** y no se unen por "
        "encima del hueco: SIPSA no publicó entre enero de 2021 y enero de 2022, y ese vacío es "
        "parte del resultado."
    )

    # --- Lo que midieron los indicadores -----------------------------------------
    st.subheader("¿Y esto se midió, o es solo mirar la gráfica?")

    medido = sensibilidad_cadena(art_id, nombres[codigo])

    if medido.empty:
        st.info(
            "Para esta combinación no hay ninguna medición en `indicador_sensibilidad_clima`. "
            "La gráfica de arriba sirve para explorar, no para concluir."
        )
    else:
        ESLABON = {
            "oni->lluvia": "El Niño / La Niña → lluvia en la zona",
            "lluvia->oferta": "lluvia → toneladas que llegan",
            "oferta->precio": "toneladas que llegan → precio",
        }
        METODO = {
            "correlacion_pearson": "correlación",
            "regresion_estacional": "regresión con temporada",
            "panel_efectos_fijos": "panel de mercados",
        }
        tabla = medido.assign(
            eslabon=medido["eslabon"].map(ESLABON).fillna(medido["eslabon"]),
            hallazgo=medido["q_valor"] < UMBRAL_Q,
            metodo=medido["metodo"].map(METODO).fillna(medido["metodo"]),
        )
        hallazgos = int(tabla["hallazgo"].sum())

        st.dataframe(
            tabla[["eslabon", "rezago_meses", "coeficiente", "q_valor", "n", "hallazgo", "metodo"]],
            column_config={
                "eslabon": "Eslabón",
                "rezago_meses": st.column_config.NumberColumn("Meses después", format="%d"),
                "coeficiente": st.column_config.NumberColumn("Efecto (negativo = baja)", format="%+.4f"),
                "q_valor": st.column_config.NumberColumn("Probabilidad de casualidad (q)", format="%.4f"),
                "n": st.column_config.NumberColumn("Meses usados", format="%d"),
                "hallazgo": st.column_config.CheckboxColumn("¿Se sostiene?"),
                "metodo": "Método",
            },
            width="stretch", hide_index=True,
            height=min(420, 36 * (len(tabla) + 1) + 3),
        )

        if hallazgos:
            st.caption(
                f"**{hallazgos} de {len(tabla)}** relaciones se sostienen: su probabilidad de ser "
                "casualidad es menor a 1 en 10. El **signo** del efecto dice la dirección: negativo en "
                "«toneladas → precio» significa que cuando llega más producto, el precio baja, que es "
                "lo que uno esperaría. «Meses después» es el rezago: cuánto tarda en aparecer el efecto."
            )
        else:
            st.caption(
                f"**Ninguna de las {len(tabla)} relaciones se sostiene**: todas tienen 1 en 10 o "
                "más de probabilidad de ser casualidad. "
                "Dicho claro: para este artículo y departamento, los datos **no alcanzan** para "
                "afirmar que el clima mueva el precio. Es un resultado válido y hay que reportarlo "
                "así, no buscar otro corte hasta que algo dé significativo."
            )

        st.caption(
            "La **probabilidad de casualidad** (en estadística, el q-valor) ya corrige por haber "
            "probado muchas parejas a la vez: con 140 pruebas, unas cuantas parecen relaciones "
            "por puro azar, y esta corrección las descuenta. "
            "El eslabón «lluvia → precio» se calculó sobre los nombres de los precios diarios, que "
            "usan otros códigos, así que no aparece acá."
        )

