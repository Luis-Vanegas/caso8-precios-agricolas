"""Semaforo: que productos y mercados se movieron raro en un mes elegido."""

import numpy as np
import streamlit as st

import estilo
import graficas
from datos import con_indicadores, fecha, mercados_geo, ultimo_mes_cerrado
from src.indicators.volatilidad import UMBRAL_AMARILLA, UMBRAL_ROJA, resumen_por_producto

estilo.aplicar()
estilo.encabezado(
    "Semáforo de alertas",
    "Cada serie (un producto en un mercado) se compara contra su propia historia. "
    "No importa si el producto es caro: importa si este mes se movió distinto a lo normal.",
)

estilo.explicacion(
    f"Calculamos cuánto cambió el precio frente al mes anterior y lo comparamos con los cambios "
    f"de todos los meses previos de esa misma serie. Si el cambio se sale más de "
    f"<b>{UMBRAL_AMARILLA:g} desviaciones</b> de lo normal, la alerta es <b>amarilla</b>; si se sale "
    f"más de <b>{UMBRAL_ROJA:g}</b>, es <b>roja</b>. Los umbrales los fijamos nosotros: no son un "
    "estándar oficial."
)

df = con_indicadores()
cerrado = ultimo_mes_cerrado()
periodos = sorted(df["periodo"].unique(), reverse=True)
periodo = st.selectbox(
    "Mes", periodos, index=periodos.index(cerrado) if cerrado in periodos else 0,
    format_func=lambda p: fecha(p) + ("  ·  en curso, parcial" if p > cerrado else ""),
)
mes = df[df["periodo"] == periodo]
if periodo > cerrado:
    st.warning("Este mes todavía no termina: tiene pocos días de datos y sus alertas pueden cambiar.")

estilo.contadores([
    ("alertas rojas", int((mes["alerta"] == "roja").sum()), "", estilo.ROJO),
    ("alertas amarillas", int((mes["alerta"] == "amarilla").sum()), "", "#B38A12"),
    ("series normales", int((mes["alerta"] == "verde").sum()), "", estilo.VERDE),
])

# --- Lista de alertas (izquierda) y mapa del mismo mes (derecha) ---------------------
izq, der = st.columns([1.1, 1], gap="large")

with izq:
    st.subheader(f"Alertas de {fecha(periodo)}")
    encendidas = mes[mes["alerta"].isin(["roja", "amarilla"])]
    encendidas = encendidas.reindex(encendidas["z_score"].abs().sort_values(ascending=False).index)
    if encendidas.empty:
        st.success("Ninguna alerta este mes.")
    else:
        tabla = encendidas.assign(
            alerta=encendidas["alerta"].astype(str),
            producto=encendidas["producto"].str.replace("*", "", regex=False),
            mercado=encendidas["mercado"].str.title(),
            cambio=(np.exp(encendidas["retorno_log"]) - 1) * 100,   # retorno logaritmico -> %
        )
        st.dataframe(
            tabla[["alerta", "producto", "mercado", "cambio", "z_score", "precio_cop_kg"]],
            column_config={
                "alerta": "Alerta", "producto": "Producto", "mercado": "Mercado",
                "cambio": st.column_config.NumberColumn("Cambio del mes", format="%+.0f%%"),
                "z_score": st.column_config.NumberColumn("z-score", format="%+.1f"),
                "precio_cop_kg": st.column_config.NumberColumn("Precio COP/kg", format="$%.0f"),
            },
            width="stretch", hide_index=True,
            height=min(560, 36 * (len(tabla) + 1) + 3),   # alto justo a las filas, sin renglones vacios
        )
        st.caption(
            "Cada fila es un producto en un mercado cuyo precio se salió de lo normal, de la más "
            "rara a la menos rara. «Cambio del mes» es lo que subió (+) o bajó (−) frente al mes "
            "anterior; el z-score dice a cuántas desviaciones de lo normal quedó."
        )

with der:
    st.subheader("¿Dónde están?")
    estilo.grafica(graficas.mapa_mercados(mes, mercados_geo()))
    st.caption(
        "Cada punto es una ciudad. Un punto grande y de color tiene alertas: rojo si hay alguna "
        "roja, amarillo si solo hay amarillas; cuantos más productos con alerta, más grande. "
        "Los puntos chicos y apagados no tienen alertas. Pasa el mouse para ver cuáles productos."
    )

# --- Ranking de volatilidad ----------------------------------------------------------
st.subheader("¿Qué productos son más volátiles en general?")
resumen = resumen_por_producto(df)
resumen["producto"] = resumen["producto"].str.replace("*", "", regex=False)
estilo.grafica(graficas.barras_horizontales(resumen, "volatilidad_mediana", "producto",
                                            "Volatilidad anualizada (mediana)"))
st.caption(
    "Cada barra es un producto: cuanto más larga, más suben y bajan sus precios en un año "
    "(mediana de todos sus mercados). Un producto muy volátil no dispara alertas seguido: "
    "para él, los saltos grandes son lo normal."
)
estilo.pie()
