"""Pronostico de precio, con una condicion: solo se muestra si le gana al modelo ingenuo.

El modelo ingenuo dice "el mes que viene va a costar lo mismo que este mes". Es
dificil de ganar, y un modelo que no le gana no aporta nada: en ese caso esta
pagina lo dice en vez de dibujarlo.
"""

import streamlit as st

import estilo
import graficas
from datos import consultar, fecha, tabla_existe

estilo.aplicar()
estilo.encabezado(
    "Pronóstico de precio",
    "Qué precio se espera para los próximos meses, y si el modelo realmente sirve.",
)

if not tabla_existe("pronostico_precio"):
    st.info(
        "**Disponible cuando se integre el modelo de pronóstico.** "
        "Esta página lee la tabla `pronostico_precio`, que todavía no está en la base. "
        "El modelo usa rezagos de lluvia, abastecimiento y el índice ONI, y se valida contra "
        "el pasado antes de publicarse."
    )
    estilo.explicacion(
        "Mientras no exista el modelo, la app no muestra ningún pronóstico. "
        "Es a propósito: es mejor no decir nada que mostrar un número inventado."
    )
    estilo.pie()
    st.stop()

estilo.explicacion(
    "Un pronóstico sin comparación no se puede juzgar. Por eso acá se mide contra el "
    "<b>modelo ingenuo</b>, que simplemente repite el último precio conocido. "
    "Si el modelo no le gana al ingenuo en los datos del pasado, <b>no se muestra</b>: "
    "se informa que no superó la prueba. El error se mide con el <b>MAE</b>, el promedio de "
    "lo que se equivoca en pesos."
)

series = consultar("""
    SELECT art_id, any_value(articulo) AS articulo, mercado,
           any_value(modelo) AS modelo,
           any_value(mae_modelo) AS mae_modelo, any_value(mae_ingenuo) AS mae_ingenuo
    FROM pronostico_precio
    GROUP BY art_id, mercado
    ORDER BY articulo, mercado
""")

if series.empty:
    st.info("La tabla `pronostico_precio` existe pero está vacía.")
    estilo.pie()
    st.stop()

series["etiqueta"] = series["articulo"] + " · " + series["mercado"].str.title()
eleccion = st.selectbox("Artículo y mercado", series.index.tolist(),
                        format_func=lambda i: series.loc[i, "etiqueta"])
fila = series.loc[eleccion]

df = consultar(f"""
    SELECT periodo, tipo, valor, lim_inf, lim_sup
    FROM pronostico_precio
    WHERE art_id = {int(fila['art_id'])} AND mercado = '{fila['mercado']}'
    ORDER BY periodo
""")

mae_modelo, mae_ingenuo = fila["mae_modelo"], fila["mae_ingenuo"]
gana = mae_modelo is not None and mae_ingenuo is not None and mae_modelo < mae_ingenuo

estilo.fila_de_tarjetas([
    estilo.tarjeta("Modelo", str(fila["modelo"] or "—"), "el que se validó"),
    estilo.tarjeta("Error del modelo", estilo.pesos(mae_modelo) if mae_modelo else "—",
                   "MAE en la validación"),
    estilo.tarjeta("Error del ingenuo", estilo.pesos(mae_ingenuo) if mae_ingenuo else "—",
                   "repetir el último precio"),
    estilo.tarjeta("¿Le gana al ingenuo?", "Sí" if gana else "No",
                   "si no, no se publica el pronóstico",
                   color=estilo.VERDE if gana else estilo.ROJO),
])

st.subheader(fila["etiqueta"])

if not gana:
    st.warning(
        f"**Este modelo no le gana al modelo ingenuo** "
        f"({estilo.pesos(mae_modelo) if mae_modelo else '—'} de error frente a "
        f"{estilo.pesos(mae_ingenuo) if mae_ingenuo else '—'}), así que su pronóstico **no se "
        "muestra**. Abajo queda solo el precio real. Un modelo que no supera a «mañana cuesta lo "
        "mismo que hoy» no agrega información, y publicarlo daría una falsa sensación de certeza."
    )
    estilo.grafica(graficas.pronostico_con_banda(df[df["tipo"] == "real"]))
else:
    estilo.grafica(graficas.pronostico_con_banda(df))
    st.caption(
        "La línea negra es el precio real; la punteada azul, el pronóstico; la banda azul, el "
        "rango probable (80 %). La línea gris vertical marca dónde termina lo observado. "
        "Cuanto más ancha la banda, menos certeza."
    )
    futuro = df[df["tipo"] == "pronostico"]
    if not futuro.empty:
        st.caption(
            f"Pronóstico de {fecha(int(futuro['periodo'].min()))} a "
            f"{fecha(int(futuro['periodo'].max()))}. "
            "Un pronóstico es un escenario probable, no una promesa: un paro, una helada o una "
            "decisión de política pueden romperlo."
        )

estilo.pie()
