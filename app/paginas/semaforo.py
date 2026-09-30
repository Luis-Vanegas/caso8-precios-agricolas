"""Semaforo: que productos y mercados se movieron raro en un mes elegido."""

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
    "Mes", periodos, index=periodos.index(cerrado),
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

tab_calor, tab_lista, tab_mapa = st.tabs(["Mapa de calor", "Lista de alertas", "Mapa animado"])

with tab_calor:
    estilo.grafica(graficas.calor_z(mes))

with tab_lista:
    encendidas = mes[mes["alerta"].isin(["roja", "amarilla"])]
    encendidas = encendidas.reindex(encendidas["z_score"].abs().sort_values(ascending=False).index)
    if encendidas.empty:
        st.success("Ninguna alerta este mes.")
    else:
        st.dataframe(
            encendidas[["alerta", "producto", "mercado", "precio_cop_kg", "z_score", "direccion", "dias_con_dato"]],
            column_config={
                "alerta": "Alerta", "producto": "Producto", "mercado": "Mercado",
                "precio_cop_kg": st.column_config.NumberColumn("Precio COP/kg", format="$%.0f"),
                "z_score": st.column_config.NumberColumn("z-score", format="%.2f"),
                "direccion": "Dirección", "dias_con_dato": "Días con dato",
            },
            width="stretch", hide_index=True,
        )

with tab_mapa:
    st.caption("Dale ▶ para ver cómo se mueven las alertas mes a mes desde 2024.")
    estilo.grafica(graficas.mapa_animado(df[df["periodo"] <= cerrado], mercados_geo(), desde=202401))

# --- Ranking de volatilidad ----------------------------------------------------------
st.subheader("¿Qué productos son más volátiles en general?")
st.caption(
    "Volatilidad anualizada típica (mediana). Un producto muy volátil no dispara alertas "
    "seguido: para él, los saltos grandes son lo normal."
)
resumen = resumen_por_producto(df)
resumen["producto"] = resumen["producto"].str.replace("*", "", regex=False)
estilo.grafica(graficas.barras_horizontales(resumen, "volatilidad_mediana", "producto",
                                            "Volatilidad anualizada (mediana)"))
estilo.pie()
