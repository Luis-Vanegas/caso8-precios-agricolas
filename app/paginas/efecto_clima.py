"""¿Cuanto afecta el clima? La respuesta al reto, con lo que se pudo medir.

Lee dos tablas de indicadores (docs/contrato_datos.md):
- indicador_sensibilidad_clima: 4 eslabones de la cadena El Nino -> lluvia ->
  toneladas -> precio. Solo cuenta como hallazgo q_valor < 0,1.
- indicador_quiebres: si el precio cambio de comportamiento cuando empezo una
  fase de El Nino o La Nina.
Y trae la grafica de la antigua pagina "La cadena" (app/secciones/cadena.py).

Todos los numeros y nombres de esta pagina salen de la base: si el pipeline se
vuelve a correr con datos nuevos, los mensajes cambian solos.
"""

import math

import pandas as pd
import streamlit as st

import estilo
from datos import (UMBRAL_Q, fecha, quiebres_resumen, sensibilidad_hallazgos,
                   sensibilidad_resumen, tabla_existe)
from secciones import cadena

estilo.aplicar()
estilo.encabezado(
    "¿Cuánto afecta el clima?",
    "Lo que pudimos medir de la cadena El Niño → lluvia → toneladas que llegan → precio, "
    "y lo que no.",
)
estilo.para_presentar(
    "Esta es la respuesta al reto: El Niño sí seca las zonas productoras, pero el efecto sobre "
    "el precio solo se sostiene en unos pocos productos.<br>"
    "<b>Si te preguntan «¿entonces el clima sube los precios?»:</b> encontramos relaciones, no "
    "causas; correlación no es causalidad, y lo decimos en la página."
)

if not (tabla_existe("indicador_sensibilidad_clima") and tabla_existe("indicador_quiebres")):
    st.info(
        "Esta página lee `indicador_sensibilidad_clima` e `indicador_quiebres`, que todavía no "
        "están en la base. Las calcula `scripts/integrar.py`."
    )
    estilo.pie()
    st.stop()

resumen = sensibilidad_resumen()
hallazgos = sensibilidad_hallazgos()
quiebres = quiebres_resumen()


def nombre(producto: str) -> str:
    """'Tomate*' -> 'Tomate'. El asterisco de SIPSA marca variedad."""
    return str(producto).replace("*", "").strip()


def lista(nombres: list[str]) -> str:
    """['a', 'b', 'c'] -> 'a, b y c'."""
    return nombres[0] if len(nombres) == 1 else ", ".join(nombres[:-1]) + " y " + nombres[-1]


def eslabon(clave: str) -> pd.Series:
    """La fila del resumen de un eslabon; con ceros si no se calculo."""
    if clave in resumen.index:
        return resumen.loc[clave]
    return pd.Series(0, index=resumen.columns)


pruebas_total = int(resumen["pruebas"].sum())

encontrado, quiebre, mes_a_mes = st.tabs([
    "Lo que encontramos",
    "¿Hubo un quiebre con El Niño?",
    "La cadena, mes a mes",
])

# --- Pestana 1: los hallazgos -------------------------------------------------------
with encontrado:
    estilo.explicacion(
        f"Hicimos <b>{pruebas_total} pruebas</b>: una por eslabón, zona, producto y rezago "
        "(de 0 a 6 meses). Solo contamos como hallazgo lo que <b>se sostiene</b>: un resultado "
        "con menos de 1 en 10 de probabilidad de ser casualidad, ya corregida por haber hecho "
        f"tantas pruebas (en la jerga, q &lt; {estilo.decimal(UMBRAL_Q)}). Con tantas pruebas, "
        "algunas salen «significativas» por puro azar; esa corrección las descuenta."
    )

    tarjetas = []

    # a) El Nino -> lluvia en las zonas productoras
    oni = eslabon("oni->lluvia")
    if oni["hallazgos"]:
        sentido = ("con El Niño llueve menos en las zonas productoras"
                   if oni["bajan"] == oni["hallazgos"] else "El Niño cambia la lluvia de las zonas")
        contrario = "; ninguna dice lo contrario" if oni["suben"] == 0 else ""
        tarjetas.append(estilo.cifra(
            f"{int(oni['hallazgos'])} de {int(oni['pruebas'])}",
            f"pruebas muestran que {sentido}{contrario}",
            f"en {int(oni['departamentos_hallazgo'])} de {int(oni['departamentos'])} zonas, "
            "de 0 a 6 meses después", color=estilo.ROJO))

    # b) lluvia -> precio: el hallazgo mas seguro
    lluvia = hallazgos[hallazgos["eslabon"] == "lluvia->precio"]
    if not lluvia.empty:
        f = lluvia.iloc[0]
        # El efecto esta en logaritmo del precio por mm/dia: exp(efecto) - 1 lo pasa a %.
        cambio = (math.exp(f["coeficiente"]) - 1) * 100
        tarjetas.append(estilo.cifra(
            f"{int(f['rezago_meses'])} meses",
            f"tarda el precio del {nombre(f['producto']).lower()} de {f['departamento']} en "
            f"reaccionar a la lluvia: si llueve 1 mm más por día (unos 30 mm más en el mes), "
            f"queda cerca de {estilo.decimal(abs(cambio), 0)} % más "
            f"{'barato' if cambio < 0 else 'caro'}",
            f"{len(lluvia)} de {int(eslabon('lluvia->precio')['pruebas'])} pruebas "
            "lluvia → precio se sostienen", retraso=1))

    # c) toneladas que llegan -> precio
    oferta = hallazgos[hallazgos["eslabon"] == "oferta->precio"]
    bajan = oferta[oferta["coeficiente"] < 0]
    suben = oferta[oferta["coeficiente"] > 0]
    if not bajan.empty:
        # Elasticidad: con 10 % mas toneladas, el precio cambia 1,1^efecto - 1.
        efectos = ((1.1 ** bajan["coeficiente"]) - 1) * 100
        tarjetas.append(estilo.cifra(
            f"{len(bajan)} de {int(eslabon('oferta->precio')['productos'])}",
            f"productos bajan de precio cuando llegan más toneladas a las centrales: "
            f"{lista([nombre(p) for p in bajan['producto']])}",
            f"10 % más toneladas → precio entre {estilo.decimal(abs(efectos.max()))} % y "
            f"{estilo.decimal(abs(efectos.min()))} % más bajo", retraso=2))

    # d) quiebre de precios al empezar El Nino
    nino = quiebres[quiebres["fase"] == "El Nino"]
    if not nino.empty:
        q = nino.iloc[0]
        cambiaron = int(q["con_quiebre"])
        tarjetas.append(estilo.cifra(
            f"{cambiaron} de {int(q['productos'])}",
            f"productos cambiaron de comportamiento cuando empezó El Niño "
            f"({fecha(int(q['periodo_quiebre']))})"
            + (": ni subieron más rápido ni se volvieron más inestables" if cambiaron == 0 else ""),
            "precio nacional, sin la temporada", retraso=3))

    estilo.fila_de_tarjetas(tarjetas, ancho_minimo=250)

    notas = []
    if not suben.empty:
        notas.append(
            f"En {lista([nombre(p).lower() for p in suben['producto']])} sale al revés: con más "
            "toneladas el precio sube un poco. No lo esperábamos y no lo sabemos explicar; lo "
            "dejamos a la vista en vez de esconderlo.")
    lluvia_oferta = eslabon("lluvia->oferta")
    if lluvia_oferta["pruebas"] and not lluvia_oferta["hallazgos"]:
        notas.append(
            f"El eslabón del medio no apareció: de {int(lluvia_oferta['pruebas'])} pruebas, "
            "ninguna muestra que la lluvia cambie las toneladas que llegan a las centrales.")
    for nota in notas:
        st.caption(nota)

    # Los productos donde la senal se sostiene, leidos de la base (no escritos a mano).
    con_senal = list(dict.fromkeys(nombre(p).lower() for p in
                                   pd.concat([lluvia["producto"], bajan["producto"]])))
    estilo.explicacion(
        "Que dos cosas se muevan juntas no prueba que una cause la otra: "
        "<b>correlación no es causalidad</b>. El precio también se mueve por el dólar, el "
        "combustible, los paros o la temporada. Lo que sí podemos decir es <b>dónde vale la pena "
        "mirar</b>"
        + (f": en {lista(con_senal)} la señal es lo bastante fuerte como para no ser casualidad."
           if con_senal else "."),
        etiqueta="Lo que esto NO dice",
    )

    st.subheader("Los cuatro eslabones, uno por uno")
    EN_PALABRAS = {
        "oni->lluvia": ("1 · El Niño → lluvia en la zona", "¿El Niño cambia cuánto llueve donde se siembra?"),
        "lluvia->oferta": ("2 · Lluvia → toneladas que llegan", "¿La lluvia cambia cuánto llega a la central?"),
        "oferta->precio": ("3 · Toneladas → precio", "¿Si llega más producto, baja el precio?"),
        "lluvia->precio": ("4 · Lluvia → precio", "¿La lluvia mueve el precio directamente?"),
    }
    filas = []
    for clave, (titulo, pregunta) in EN_PALABRAS.items():
        e = eslabon(clave)
        filas.append({"Eslabón": titulo, "La pregunta": pregunta,
                      "Pruebas": int(e["pruebas"]), "Se sostienen": int(e["hallazgos"])})
    st.dataframe(pd.DataFrame(filas), width="stretch", hide_index=True)

    with st.expander("Ver cada hallazgo con sus números"):
        tabla = hallazgos.assign(
            eslabon=hallazgos["eslabon"].map(lambda c: EN_PALABRAS.get(c, (c,))[0]),
            producto=hallazgos["producto"].map(lambda p: nombre(p) if pd.notna(p) else "—"),
            departamento=hallazgos["departamento"].fillna("todas las zonas (panel)"),
        )
        st.dataframe(
            tabla[["eslabon", "producto", "departamento", "rezago_meses", "coeficiente", "q_valor", "n"]],
            column_config={
                "eslabon": "Eslabón", "producto": "Producto", "departamento": "Zona",
                "rezago_meses": st.column_config.NumberColumn("Meses después", format="%d"),
                "coeficiente": st.column_config.NumberColumn(
                    "Efecto (negativo = baja)", format="%+.3f"),
                "q_valor": st.column_config.NumberColumn(
                    "Probabilidad de casualidad (q)", format="%.4f"),
                "n": st.column_config.NumberColumn("Meses usados", format="%d"),
            },
            width="stretch", hide_index=True,
        )
        st.caption(
            "El **efecto** se lee por su signo: negativo quiere decir que cuando sube lo primero, "
            "baja lo segundo. En «El Niño → lluvia» es una correlación (de −1 a 1); en "
            "«toneladas → precio», cuánto cambia el precio en % por cada 1 % más de toneladas; en "
            "«lluvia → precio», el cambio del precio (en logaritmo) por cada mm de lluvia al día. "
            "La **probabilidad de casualidad** es el q-valor: el p-valor corregido por haber "
            "hecho muchas pruebas."
        )

# --- Pestana 2: quiebres -------------------------------------------------------------
with quiebre:
    estilo.explicacion(
        "Un <b>quiebre</b> sería que, a partir de una fecha, el precio de un producto empiece a "
        "subir más rápido (cambia su <b>ritmo</b>) o a saltar más (cambia su <b>volatilidad</b>). "
        "Probamos las fechas en que empezó cada fase del clima, con el precio nacional de cada "
        "producto frente a la canasta y sin la temporada, para no confundir inflación o época de "
        "cosecha con clima."
    )
    vista = pd.DataFrame({
        "Fecha probada": quiebres["periodo_quiebre"].map(lambda p: fecha(int(p))),
        "Qué empezó": quiebres["fase"].map(estilo.fase_legible).map(
            lambda f: "fase neutral" if f == "Neutral" else f),
        "Productos": quiebres["productos"],
        "Cambiaron su ritmo": quiebres["ritmo"],
        "Cambiaron su volatilidad": quiebres["volatilidad"],
    })
    st.dataframe(vista, width="stretch", hide_index=True)
    sin_corregir = int(quiebres["ritmo_p"].sum() + quiebres["volatilidad_p"].sum())
    pruebas_quiebre = int(2 * quiebres["productos"].sum())
    st.caption(
        f"Se cuentan los quiebres que se sostienen (probabilidad de casualidad menor a 1 en 10). "
        f"Sin esa corrección aparecen {sin_corregir} de {pruebas_quiebre} pruebas con un p-valor "
        "pequeño, que es justo lo que se espera por azar al hacer tantas pruebas."
    )
    if not quiebres.empty and int(quiebres["con_quiebre"].sum()) == 0:
        st.success(
            "**No hubo un quiebre de precios al empezar El Niño** (ni en las otras fechas). "
            "Es un resultado válido: con estos datos, los precios no cambiaron de "
            "comportamiento de golpe cuando cambió el clima."
        )

# --- Pestana 3: la cadena (antes pagina "La cadena") -------------------------------
with mes_a_mes:
    cadena.mostrar()

estilo.pie()
