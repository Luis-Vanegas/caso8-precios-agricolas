"""Mapa por departamento: donde subio y donde bajo el precio de un articulo.

El mapa colorea por VARIACION %, nunca por nivel de precio. La razon esta en
docs/contrato_datos.md: la misma "papa" es otra variedad en cada ciudad, asi que
comparar niveles entre departamentos compara productos distintos.
"""

import streamlit as st

import estilo
import graficas
from datos import (MINIMO_DEPARTAMENTOS, articulos_del_mapa, fecha, geojson_departamentos,
                   periodos_semanal, variacion_departamentos)

estilo.aplicar()
estilo.encabezado(
    "Mapa por departamento",
    "Cuánto cambió el precio de un artículo en cada departamento frente al mes anterior.",
)

estilo.explicacion(
    "El color dice <b>cuánto cambió</b> el precio, no cuán caro es. "
    "Y es a propósito: la «papa» de Bogotá y la de Barranquilla son variedades distintas, "
    "así que comparar sus precios compararía productos distintos. El cambio porcentual sí se "
    "puede comparar, porque cada departamento se compara contra sí mismo. "
    f"Un artículo que se vende en menos de {MINIMO_DEPARTAMENTOS} departamentos no aparece: "
    "con dos puntos no hay nada que leer en un mapa."
)

articulos = articulos_del_mapa()
meses = periodos_semanal()

if articulos.empty or meses.empty:
    st.info(
        "El mapa necesita la tabla `fact_precio_semanal`, que llega con la fuente de precios "
        "semanales. Todavía no está en la base."
    )
    st.stop()

izq, der = st.columns([2, 1], gap="large")
with izq:
    opciones = articulos["art_id"].tolist()
    etiquetas = dict(zip(articulos["art_id"], articulos["articulo"]))
    art_id = st.selectbox("Artículo", opciones, format_func=lambda a: etiquetas[a],
                          index=opciones.index(159) if 159 in opciones else 0)
with der:
    # Por defecto el ultimo mes completo: el mes en curso trae una o dos semanas
    # y su variacion contra un mes de cuatro no es comparable.
    completos = meses[~meses["parcial"]]["periodo"].tolist()
    opciones_mes = meses["periodo"].tolist()
    parcial = dict(zip(meses["periodo"], meses["parcial"]))
    periodo = st.selectbox(
        "Mes", opciones_mes,
        index=opciones_mes.index(completos[0]) if completos else 0,
        format_func=lambda p: fecha(p) + ("  ·  en curso, parcial" if parcial[p] else ""),
    )

if parcial[periodo]:
    semanas = int(meses.loc[meses["periodo"] == periodo, "semanas"].iloc[0])
    st.warning(
        f"**{fecha(periodo)} todavía no termina**: solo tiene {semanas} semana(s) de datos "
        "frente a las 4 de un mes completo, así que la variación puede cambiar."
    )

df = variacion_departamentos(art_id, periodo)
articulo = etiquetas[art_id]

if df.empty:
    st.info(f"**{articulo}** no tiene precio en {fecha(periodo)} ni en el mes anterior, "
            "así que no hay variación que mostrar. Probá otro mes.")
    st.stop()

subieron = int((df["variacion"] > 0).sum())
bajaron = int((df["variacion"] < 0).sum())
unidad = df["unidad"].iloc[0]
estilo.fila_de_tarjetas([
    estilo.tarjeta("Departamentos con dato", f"{len(df)} de 33",
                   f"precio por {unidad}"),
    estilo.tarjeta("Subió", f"{subieron}", "departamentos", color=estilo.ROJO if subieron else None),
    estilo.tarjeta("Bajó", f"{bajaron}", "departamentos", color=estilo.AZUL if bajaron else None),
    estilo.tarjeta("El que más se movió", f"{df['variacion'].abs().max():+.1f}%".replace("+-", "-"),
                   df.reindex(df["variacion"].abs().sort_values(ascending=False).index)
                     ["departamento"].iloc[0]),
])

st.subheader(f"{articulo} · {fecha(periodo)}")
estilo.grafica(graficas.mapa_departamentos(df, geojson_departamentos()))
st.caption(
    "**Rojo**: el precio subió. **Azul**: bajó. **Blanco**: casi no cambió. **Gris claro**: "
    "sin dato; ese departamento no tiene mercado que venda este artículo, o le falta el mes "
    "anterior para comparar. Se dibuja igual para que el mapa muestre el país completo. Cuando un departamento tiene varios mercados "
    "(Antioquia tiene 11), el valor es la **mediana** de sus variaciones, nunca el promedio de "
    "sus precios. Pasá el mouse para ver el dato exacto."
)

st.subheader("El detalle, en números")
st.dataframe(
    df[["departamento", "variacion", "mercados"]],
    column_config={
        "departamento": "Departamento",
        "variacion": st.column_config.NumberColumn("Cambio del mes", format="%+.1f%%"),
        "mercados": st.column_config.NumberColumn("Mercados", format="%d"),
    },
    width="stretch", hide_index=True, height=min(520, 36 * (len(df) + 1) + 3),
)
st.caption(
    "Los precios semanales son una **ventana móvil**: la API del DANE solo entrega los últimos "
    "doce meses, así que este mapa no llega más atrás. El proyecto va guardando cada descarga "
    "para que la historia crezca de aquí en adelante."
)

estilo.pie()
