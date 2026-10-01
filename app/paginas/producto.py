"""Detalle: la historia de precio de un producto en un mercado."""

import numpy as np
import pandas as pd
import streamlit as st

import estilo
import graficas
from datos import con_indicadores, fecha, puente, ultimo_mes_cerrado

estilo.aplicar()
estilo.encabezado(
    "Detalle por producto",
    "Escoge un producto y un mercado para ver su precio mes a mes, qué tan raro fue cada "
    "cambio y si se puede comparar con los datos de la FAO.",
)

df = con_indicadores()
c1, c2 = st.columns(2)
productos = sorted(df["producto"].unique())
producto = c1.selectbox("Producto", productos, index=productos.index("Papa negra*") if "Papa negra*" in productos else 0)
mercados = sorted(df.loc[df["producto"] == producto, "mercado"].unique())
mercado = c2.selectbox("Mercado", mercados, index=mercados.index("BOGOTÁ, D.C.") if "BOGOTÁ, D.C." in mercados else 0)

serie = df[(df["producto"] == producto) & (df["mercado"] == mercado)].sort_values("periodo")
if serie.empty:
    st.warning("No hay datos para esa combinación.")
    st.stop()

# --- Resumen en tarjetas ----------------------------------------------------------
cerrado = serie[serie["periodo"] <= ultimo_mes_cerrado()]
if cerrado.empty:                      # serie que solo tiene el mes abierto
    cerrado = serie
ultimo = cerrado.iloc[-1]
# El mismo mes del ano pasado, buscado por fecha: contar 12 filas atras fallaria
# si la serie tiene huecos (por ejemplo, 2021).
anterior = cerrado[cerrado["periodo"] == ultimo["periodo"] - 100]
cambio_anual = None                    # None = no hay precio de hace un ano
if not anterior.empty and anterior["precio_cop_kg"].iloc[0] > 0:
    cambio_anual = ultimo["precio_cop_kg"] / anterior["precio_cop_kg"].iloc[0] - 1
vol = ultimo["volatilidad_anualizada"]

estilo.fila_de_tarjetas([
    estilo.tarjeta(f"Precio en {fecha(int(ultimo['periodo']))}", estilo.pesos(ultimo["precio_cop_kg"]) + "/kg",
                   f"promedio de {int(ultimo['dias_con_dato'])} días con dato", retraso=0),
    estilo.tarjeta("Frente a hace un año", "sin dato" if cambio_anual is None else f"{cambio_anual:+.0%}",
                   f"vs {fecha(int(ultimo['periodo']) - 100)}", retraso=1),
    estilo.tarjeta("Volatilidad anualizada", "sin dato" if pd.isna(vol) else f"{vol:.0%}",
                   "desviación de 12 meses × √12", retraso=2),
    estilo.tarjeta("Meses con alerta", str(int(serie["alerta"].isin(["roja", "amarilla"]).sum())),
                   f"de {len(serie)} meses con dato", retraso=3),
])

# --- Graficas ------------------------------------------------------------------------
estilo.grafica(graficas.serie_precio(serie))
st.caption(
    "La línea verde es el precio promedio de cada mes (eje vertical, en pesos por kilo) y la banda "
    "clara va del precio más bajo al más alto de ese mes. Un círculo amarillo o rojo marca un mes "
    "con alerta. Donde la línea se corta no hay datos."
)
estilo.grafica(graficas.z_score(serie))
estilo.explicacion(
    "Cada barra es un mes. Si queda en la franja blanca, el cambio de precio fue normal para "
    "este producto en este mercado. Si entra en la franja amarilla o roja, fue un cambio raro "
    "y se enciende la alerta. Los huecos son meses sin dato (por ejemplo, todo 2021)."
)

# --- Se puede comparar con FAOSTAT? ---------------------------------------------
fila = puente()[puente()["producto_sipsa"] == producto]
if not fila.empty:
    f = fila.iloc[0]
    st.subheader("¿Se puede comparar con el precio al productor de la FAO?")
    if f["permite_comparar_precio"]:
        st.success(f"Sí. Corresponde exactamente al ítem {f['item_codigo_fao']} de FAOSTAT ({f['item_fao']}).")
    elif pd.isna(f["item_codigo_fao"]):
        st.error("No. FAOSTAT no publica este producto para Colombia.")
    else:
        st.warning(
            f"Solo en parte. FAOSTAT lo mete en el ítem {f['item_codigo_fao']} ({f['item_fao']}) "
            "junto con otros productos, así que ese precio es una mezcla y no sirve para comparar."
        )

with st.expander("Ver la tabla completa"):
    st.dataframe(
        serie[["periodo", "precio_cop_kg", "precio_min", "precio_max", "dias_con_dato",
               "retorno_log", "volatilidad_anualizada", "z_score", "alerta"]],
        width="stretch", hide_index=True,
    )
estilo.pie()
