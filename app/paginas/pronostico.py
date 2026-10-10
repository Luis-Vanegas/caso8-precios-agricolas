"""Pronostico de precio y, sobre todo, si se le puede creer.

El modelo ingenuo dice "el mes que viene va a costar lo mismo que este mes". Es
dificil de ganar. Esta pagina muestra el pronostico y al lado el veredicto:
cuanto se equivoca el modelo y si le gana al ingenuo. Cuando no le gana, lo que
se publica es el ingenuo, y la pagina lo dice.
"""

import streamlit as st

import estilo
import graficas
from datos import consultar, fecha, tabla_existe

estilo.aplicar()
estilo.encabezado(
    "Pronóstico de precio",
    "Qué precio se espera para los próximos meses, y qué tanto se le puede creer.",
)
estilo.para_presentar(
    "Aquí está el precio esperado de los próximos 3 meses y, al lado, cuánto se equivoca el "
    "modelo comparado con repetir el último precio.<br>"
    "<b>Si te preguntan «¿y por qué a veces muestran el ingenuo?»:</b> porque si el modelo no "
    "le gana a lo más simple, publicarlo sería inventar certeza."
)

if not tabla_existe("pronostico_precio"):
    st.info(
        "**Disponible cuando se integre el modelo de pronóstico.** "
        "Esta página lee la tabla `pronostico_precio`, que todavía no está en la base."
    )
    estilo.pie()
    st.stop()

estilo.explicacion(
    "Un pronóstico sin comparación no se puede juzgar. Acá se compara contra los modelos "
    "<b>ingenuos</b>: «el mes que viene cuesta lo mismo que este» y «cuesta lo mismo que el "
    "año pasado en este mes». El error se mide como <b>cuánto se equivoca en promedio, en "
    "porcentaje del precio</b> (en la jerga, MAE), sobre 24 meses de prueba. Si el modelo no le gana al mejor ingenuo por al menos 5 %, "
    "<b>lo que se publica es el ingenuo</b>, no el modelo."
)

productos = consultar("SELECT DISTINCT producto FROM pronostico_precio ORDER BY producto")
if productos.empty:
    st.info("La tabla `pronostico_precio` existe pero está vacía.")
    estilo.pie()
    st.stop()

opciones = productos["producto"].tolist()
producto = st.selectbox("Producto", opciones,
                        format_func=lambda p: p.replace("*", ""),
                        index=opciones.index("Papa criolla") if "Papa criolla" in opciones else 0)
nombre = producto.replace("*", "")

df = consultar(f"""
    SELECT periodo, horizonte, tipo, valor, lim_inf, lim_sup, modelo,
           mae_modelo, mae_ingenuo, gana_al_ingenuo
    FROM pronostico_precio
    WHERE producto = '{producto.replace("'", "''")}'
    ORDER BY periodo, horizonte
""")

# El veredicto es por horizonte: un modelo puede servir a un mes y no a tres.
veredicto = (df[df["tipo"] == "pronostico"]
             .groupby("horizonte")
             .agg(modelo=("modelo", "first"), mae_modelo=("mae_modelo", "first"),
                  mae_ingenuo=("mae_ingenuo", "first"),
                  gana=("gana_al_ingenuo", "first"),
                  periodo=("periodo", "first"))
             .reset_index())

gana_alguno = bool(veredicto["gana"].any()) if not veredicto.empty else False

st.subheader(nombre)

# Nombres de los modelos en palabras (la tabla los trae como codigos).
MODELO = {"regresion": "regresión con clima", "sin_cambio": "ingenuo: igual que este mes",
          "estacional": "ingenuo: igual que hace un año"}

if not veredicto.empty:
    estilo.fila_de_tarjetas([
        estilo.tarjeta(
            f"A {int(f.horizonte)} mes" + ("es" if f.horizonte > 1 else ""),
            f"{estilo.decimal(f.mae_modelo)} %",
            f"se equivoca en promedio; el ingenuo, {estilo.decimal(f.mae_ingenuo)} %  ·  "
            f"se publica: {MODELO.get(f.modelo, f.modelo)}",
            color=estilo.VERDE if f.gana else estilo.ROJO,
        )
        for f in veredicto.itertuples()
    ])
    st.caption(
        "Cada tarjeta es un horizonte. El número es **cuánto se equivoca en promedio**, en "
        "porcentaje: más bajo es mejor. **Verde** significa que el modelo le ganó al ingenuo por "
        "al menos 5 %; **rojo**, que no, y en ese caso lo que se publica abajo es el ingenuo."
    )

if not gana_alguno:
    st.warning(
        f"**Para {nombre} el modelo no le gana a los ingenuos en ningún horizonte.** "
        "Lo que se grafica abajo es el modelo ingenuo, que es lo mejor disponible. "
        "Dicho sin vueltas: para este producto el proyecto **no sabe pronosticar mejor** que "
        "repetir el último precio, y mostrar otra cosa sería inventar certeza."
    )

estilo.grafica(graficas.pronostico_con_banda(df))

st.caption(
    "Línea negra: el precio real; se corta en 2021 porque SIPSA no publicó de enero de 2021 a "
    "enero de 2022, y ese hueco se muestra, no se rellena. Línea gris punteada: **lo que el modelo habría pronosticado "
    "mes a mes en el pasado** (ahí se ve cuánto le atina de verdad). Línea azul punteada con "
    "banda: el pronóstico de los próximos meses, con su rango probable del 80 %. "
    "La vertical gris marca dónde termina lo observado."
)

futuro = df[df["tipo"] == "pronostico"]
if not futuro.empty:
    st.caption(
        f"Pronóstico de {fecha(int(futuro['periodo'].min()))} a "
        f"{fecha(int(futuro['periodo'].max()))}, para el precio **nacional** (la mediana de los "
        "mercados), no para una ciudad en particular. "
        "Un pronóstico es un escenario probable, no una promesa: un paro, una helada o una "
        "decisión de política pueden romperlo. Y la banda se ensancha con el horizonte porque "
        "la incertidumbre crece."
    )

estilo.pie()
