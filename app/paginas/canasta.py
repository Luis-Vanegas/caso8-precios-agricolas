"""Semaforo de la canasta: como se movieron los precios, mes por mes.

Dos pestanas, porque hay dos fuentes con productos distintos:
- Canasta familiar (precio semanal): arroz, huevo, pollo, carnes, aceite,
  panela, queso... ~286 articulos, pero solo unos 13 meses de historia.
- Frutas y verduras (precio diario): los 33 productos del semaforo de
  alertas, con historia desde 2020.

La pagina "Semaforo de alertas" responde "que paso este mes". Esta responde
"que paso en todos los meses": una celda por producto y mes.
"""

import streamlit as st

import estilo
import graficas
from datos import (cobertura_canasta, fecha, fecha_dia, matriz_canasta, periodos_semanal,
                   tabla_existe, ultimo_mes_cerrado, variacion_canasta)

estilo.aplicar()
estilo.encabezado(
    "Semáforo de la canasta",
    "Cada celda es un producto en un mes. El color dice cuánto se movió su precio.",
)

TODOS = "Todos los grupos"

pestana_familiar, pestana_diaria = st.tabs([
    "Canasta familiar · precio semanal",
    "Frutas y verduras · precio diario (desde 2020)",
])

# --- Pestana 1: canasta familiar con el precio semanal -------------------------------
with pestana_familiar:
    if not tabla_existe("fact_precio_semanal"):
        st.info("Esta vista necesita la tabla `fact_precio_semanal`, que todavía no está en la base.")
    else:
        cobertura = cobertura_canasta()
        variacion = variacion_canasta()
        meses = periodos_semanal()
        parcial = dict(zip(meses["periodo"], meses["parcial"]))

        estilo.explicacion(
            "Esta es la <b>canasta familiar</b>: arroz, huevo, pollo, carnes, aceite, panela, "
            "queso y el resto de artículos que el DANE marca como canasta. Cada celda dice "
            "<b>cuánto cambió el precio frente al mes anterior</b>: rojo subió, azul bajó. "
            "Un artículo se vende en varios mercados; su valor es la <b>mediana</b> de los cambios "
            "de sus mercados, nunca el promedio de precios de ciudades distintas."
        )

        # El periodo se lee de la base: la ventana del DANE se corre cada semana.
        st.info(
            f"**Periodo cubierto: del {fecha_dia(cobertura['desde'])} al "
            f"{fecha_dia(cobertura['hasta'])}** (semanas de precios del SIPSA semanal). "
            "La API del DANE solo entrega los últimos doce meses, así que esta vista no llega "
            "más atrás. El primer mes no tiene cambio: le falta el mes anterior para comparar."
        )

        grupos = sorted(variacion["grupo_dane"].dropna().unique())
        grupo = st.selectbox("Grupo de alimentos", [TODOS] + grupos)

        if grupo == TODOS:
            # Un grupo es la mediana de los cambios de sus articulos (regla 2 del
            # contrato de datos): nunca el promedio de sus precios.
            filas = (variacion.groupby(["grupo_dane", "periodo"])
                     .agg(variacion=("variacion", "median"), articulos=("art_id", "nunique"))
                     .reset_index().rename(columns={"grupo_dane": "fila"}))
            filas["detalle"] = filas.apply(
                lambda f: f"{f['variacion']:+.1f}% · mediana de {f['articulos']} artículos", axis=1)
        else:
            filas = variacion[variacion["grupo_dane"] == grupo].assign(
                fila=lambda d: d["articulo"] + " (" + d["unidad"] + ")")
            filas["detalle"] = filas.apply(
                lambda f: f"{f['variacion']:+.1f}% · mediana de {f['mercados']} mercado(s)", axis=1)

        # Columnas: todos los meses con cambio, en orden del calendario.
        periodos = sorted(variacion["periodo"].unique())
        tabla = filas.pivot(index="fila", columns="periodo", values="variacion").reindex(columns=periodos)
        detalle = (filas.pivot(index="fila", columns="periodo", values="detalle")
                   .reindex(index=tabla.index, columns=periodos).fillna("sin dato este mes"))
        etiquetas = [fecha(p) + (" (parcial)" if parcial.get(p) else "") for p in periodos]

        cerrados = [p for p in periodos if not parcial.get(p)]
        ultimo = cerrados[-1] if cerrados else periodos[-1]
        del_ultimo = variacion[variacion["periodo"] == ultimo]
        subieron = int((del_ultimo["variacion"] > 0).sum())
        bajaron = int((del_ultimo["variacion"] < 0).sum())

        estilo.fila_de_tarjetas([
            estilo.tarjeta("Artículos de la canasta", f"{int(cobertura['articulos'])}",
                           f"en {int(cobertura['mercados'])} mercados"),
            estilo.tarjeta("Meses con cambio", f"{len(periodos)}",
                           f"{fecha(periodos[0])} a {fecha(periodos[-1])}"),
            estilo.tarjeta(f"Subieron en {fecha(ultimo)}", f"{subieron}", "artículos",
                           color=estilo.ROJO if subieron else None),
            estilo.tarjeta(f"Bajaron en {fecha(ultimo)}", f"{bajaron}", "artículos",
                           color=estilo.AZUL if bajaron else None),
        ])

        estilo.grafica(graficas.matriz_variacion(tabla, etiquetas, detalle))
        st.caption(
            "**Rojo**: el precio subió frente al mes anterior. **Azul**: bajó. **Blanco**: casi "
            "no cambió. Una celda vacía no tiene dato ese mes. Un mes marcado «parcial» todavía "
            "no termina: tiene pocas semanas y su cambio puede moverse. Los porcentajes no "
            "dependen de la unidad (kg, unidad o litro), por eso se pueden poner juntos."
        )

        st.subheader(f"Lo que más se movió en {fecha(ultimo)}")
        if grupo != TODOS:
            del_ultimo = del_ultimo[del_ultimo["grupo_dane"] == grupo]
        top = del_ultimo.reindex(del_ultimo["variacion"].abs().sort_values(ascending=False).index).head(10)
        st.dataframe(
            top[["articulo", "grupo_dane", "unidad", "variacion", "mercados"]],
            column_config={
                "articulo": "Artículo", "grupo_dane": "Grupo", "unidad": "Unidad",
                "variacion": st.column_config.NumberColumn("Cambio del mes", format="%+.1f%%"),
                "mercados": st.column_config.NumberColumn("Mercados", format="%d"),
            },
            width="stretch", hide_index=True, height=min(420, 36 * (len(top) + 1) + 3),
        )

# --- Pestana 2: frutas y verduras con el precio diario --------------------------------
with pestana_diaria:
    estilo.explicacion(
        "Estos son los <b>33 productos del precio diario</b> (frutas, verduras y tubérculos), "
        "con historia desde 2020. Cada celda muestra la <b>alerta</b> del mes: un producto se "
        "vende en varios mercados y cada mercado tiene su propia alerta, así que la celda muestra "
        "la <b>peor alerta del mes</b>, porque un semáforo avisa por el caso más grave, no por el "
        "promedio. Pasá el mouse por una celda para ver en cuántos mercados se encendió."
    )

    cerrado = ultimo_mes_cerrado()
    anio_final = cerrado // 100
    anios = list(range(2020, anio_final + 1))
    desde_anio, hasta_anio = st.select_slider(
        "Años que se muestran", options=anios, value=(max(2020, anio_final - 2), anio_final),
    )

    peor, glifos, detalle_diario, etiquetas_diario = matriz_canasta(
        desde_anio * 100 + 1, hasta_anio * 100 + 12)

    meses_con_alerta = int((peor > 0).sum().sum())
    estilo.fila_de_tarjetas([
        estilo.tarjeta("Productos", f"{len(peor)}", "los que publica SIPSA a diario"),
        estilo.tarjeta("Meses mostrados", f"{len(etiquetas_diario)}",
                       f"hasta {fecha(cerrado)} (último mes cerrado)"),
        estilo.tarjeta("Celdas en alerta", f"{meses_con_alerta}",
                       "producto-mes con alerta amarilla o roja",
                       color=estilo.AMARILLO if meses_con_alerta else estilo.VERDE),
    ])

    estilo.grafica(graficas.matriz_semaforo(peor, glifos, detalle_diario, etiquetas_diario))

    st.caption(
        "**▲ roja** · **● amarilla** · celda verde lisa: sin alerta · celda **blanca**: ese mes no "
        "tiene dato. La franja blanca de 2021 es el hueco de SIPSA (enero de 2021 a enero de "
        "2022): la fuente no publicó, y un hueco se muestra como hueco, nunca se rellena."
    )
    st.caption(
        "Leer una fila de izquierda a derecha muestra la historia de un producto; leer una "
        "columna hacia abajo muestra qué pasó en el mercado ese mes. Varias celdas encendidas en "
        "la misma columna sugieren una causa común (clima, combustible, paro), pero esta página "
        "no lo demuestra: **correlación no es causalidad**."
    )

estilo.pie()
