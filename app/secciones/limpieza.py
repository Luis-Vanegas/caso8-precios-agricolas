"""Limpieza y nulos: que se le hizo a cada tabla, por que, y cuantos datos faltan.

Los numeros de nulos se leen de docs/perfilado.md, que escribe scripts/preparar.py
en cada corrida: si se vuelve a preparar, esta pestana se actualiza sola.
Los textos (que se hizo y por que) viven en limpieza_contenido.py.
"""

import re

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import estilo
from secciones import limpieza_contenido as txt
from src.common.rutas import RAIZ

PERFILADO = RAIZ / "docs" / "perfilado.md"

# Que filas de CAMBIOS aplican a cada tabla (la columna "fuente" de CAMBIOS).
# "Todas" aplica siempre. zonas_puente no se limpia: se arma desde la configuracion.
FUENTES_DE = {
    "faostat": ["FAOSTAT"],
    "sipsa_diario": ["SIPSA diario", "SIPSA diario/mensual"],
    "sipsa_mensual": ["SIPSA mensual", "SIPSA diario/mensual"],
    "sipsa_semanal": ["SIPSA semanal", "SIPSA semanal / abastecimiento"],
    "sipsa_abastecimiento": ["SIPSA abastecimiento", "SIPSA semanal / abastecimiento"],
    "clima": ["NASA POWER"],
    "clima_diario": ["Open-Meteo"],
    "clima_estacional": ["Open-Meteo"],
    "enso": ["ONI"],
    "insumos": ["Pink Sheet"],
    "ideam": ["IDEAM"],
}

# Por que hay nulos, solo donde el codigo o la documentacion lo explican.
MOTIVO_NULOS = {
    ("sipsa_mensual", "item_codigo_fao"): "Productos sin equivalente en FAOSTAT (tipo «sin_equivalente»)",
    ("sipsa_mensual", "item_fao"): "Productos sin equivalente en FAOSTAT (tipo «sin_equivalente»)",
    ("sipsa_mensual", "nota"): "La nota de la homologación es opcional",
    ("clima", "dias_con_dato"): "Solo existe en los meses tomados del endpoint diario de NASA",
    ("faostat_qcl", "valor"): "FAOSTAT no reporta el valor ese año; se deja vacío, no se rellena",
    ("insumos", "valor_usd"): "El Pink Sheet trae «…» cuando no hay precio; se convierte en vacío",
    ("faostat_pe", "unidad"): "Columna vacía en la fuente",
    ("faostat_fbs", "nota"): "Columna vacía en la fuente",
}
CRUDOS_IDEAM = ("fechaobservacion", "valorobservado", "zonahidrografica", "descripcionsensor", "unidadmedida")


def _motivo(tabla: str, columna: str) -> str:
    if (tabla, columna) in MOTIVO_NULOS:
        return MOTIVO_NULOS[(tabla, columna)]
    if tabla == "ideam_estaciones" and columna in CRUDOS_IDEAM:
        return "Campo crudo de IDEAM casi vacío; se conserva por trazabilidad"
    return "Sin motivo documentado todavía"


@st.cache_data
def perfilado() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(resumen por tabla, una fila por columna) leidos de docs/perfilado.md."""
    if not PERFILADO.exists():
        return pd.DataFrame(), pd.DataFrame()
    resumen, columnas = [], []
    for linea in PERFILADO.read_text(encoding="utf-8").splitlines():
        # Despues de las columnas vienen otras tablas (homologacion, inconsistencias) que no son de aca.
        if linea.startswith("## Homologacion"):
            break
        if not linea.startswith("| ") or ":---" in linea or "---|" in linea:
            continue
        c = [x.strip() for x in linea.strip("|").split("|")]
        if len(c) == 4 and c[0] != "tabla":
            resumen.append({"tabla": c[0], "filas": int(c[1].replace(",", "")),
                            "columnas": int(c[2]), "duplicados": int(c[3].replace(",", ""))})
        elif len(c) == 9 and c[0] != "tabla":
            minimo, maximo = c[7], c[8]
            columnas.append({
                "tabla": c[0], "columna": c[1], "tipo": c[2],
                "descripción": txt.DESCRIPCION_POR_TABLA.get((c[0], c[1]), txt.DESCRIPCION.get(c[1], "")),
                "filas": int(c[3]), "nulos": int(c[4]), "% nulos": float(c[5]), "valores únicos": int(c[6]),
                "rango": "" if minimo in ("", "nan") else f"{minimo} a {maximo}",
            })
    return pd.DataFrame(resumen), pd.DataFrame(columnas)


def _cambios_de(tabla: str) -> pd.DataFrame:
    """Filas de CAMBIOS que aplican a una tabla."""
    clave = "faostat" if tabla.startswith("faostat") else "ideam" if tabla.startswith("ideam") else tabla
    fuentes = FUENTES_DE.get(clave, []) + ["Todas"]
    filas = [f for f in txt.CAMBIOS if f[0] in fuentes]
    return pd.DataFrame(filas, columns=["Fuente", "Dato", "Qué se modificó", "Por qué", "Con qué quedamos"])


def mostrar() -> None:
    """Resumen de nulos, pasos de limpieza, detalle por tabla y lista de cambios."""
    resumen, columnas = perfilado()
    if resumen.empty:
        st.info("Todavía no hay perfilado: corre `scripts/preparar.py` para generarlo.")
        return

    estilo.explicacion(
        "Limpiar es dejar cada dato <b>en un formato que se pueda comparar</b> sin cambiar lo que dice. "
        "Aquí ves, para cada tabla, <b>qué se le hizo, por qué</b>, y <b>cuántos valores faltan</b> (nulos). "
        "Un nulo es una casilla vacía: no lo rellenamos con un número inventado, lo dejamos vacío y lo declaramos."
    )

    # --- Cifras generales ------------------------------------------------------------------
    con_nulos = columnas[columnas["nulos"] > 0]
    estilo.fila_de_tarjetas([
        estilo.cifra(f"{len(resumen)}", "tablas limpias", "una por fuente o tema"),
        estilo.cifra(f"{resumen['filas'].sum():,}".replace(",", "."), "filas en total", "suma de todas las tablas"),
        estilo.cifra(f"{len(columnas)}", "columnas documentadas", "con tipo, descripción y nulos"),
        estilo.cifra(f"{len(con_nulos)}", "columnas con nulos", f"de {len(columnas)}; ninguna se rellenó"),
        estilo.cifra(f"{int(resumen['duplicados'].sum())}", "filas duplicadas", "por la llave de cada tabla"),
    ], ancho_minimo=190)

    # --- Paso a paso general -----------------------------------------------------------------
    st.subheader("El paso a paso, igual para todas las fuentes")
    st.dataframe(
        pd.DataFrame(txt.PASOS, columns=["Paso", "Etapa", "Qué se hace", "Dónde está el código", "Resultado"]),
        width="stretch", hide_index=True,
        column_config={"Paso": st.column_config.NumberColumn(width="small")},
    )

    # --- Detalle de una tabla ------------------------------------------------------------------
    st.subheader("Mira una tabla por dentro")
    por_nombre = {f[0]: f for f in txt.TABLAS}
    tabla = st.selectbox("Tabla", list(resumen["tabla"]), key="limpieza_tabla")
    info = por_nombre.get(tabla)
    fila = resumen[resumen["tabla"] == tabla].iloc[0]
    if info:
        st.markdown(f"**{info[1]}** · {info[2]}. Llave que identifica cada fila: `{info[3]}`.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Filas", f"{fila['filas']:,}".replace(",", "."))
    c2.metric("Columnas", int(fila["columnas"]))
    c3.metric("Duplicados por llave", int(fila["duplicados"]))

    detalle = columnas[columnas["tabla"] == tabla].drop(columns=["tabla", "filas"]).reset_index(drop=True)
    st.markdown("**Las columnas y cuántos nulos tiene cada una**")
    st.dataframe(
        detalle, width="stretch", hide_index=True,
        column_config={
            "% nulos": st.column_config.ProgressColumn("% nulos", min_value=0, max_value=100, format="%.2f %%"),
            "nulos": st.column_config.NumberColumn("nulos", format="%d"),
        },
    )
    nulos_tabla = detalle[detalle["nulos"] > 0].sort_values("% nulos")
    if nulos_tabla.empty:
        st.success("Esta tabla no tiene ningún valor vacío.")
    else:
        fig = go.Figure(go.Bar(
            x=nulos_tabla["% nulos"], y=nulos_tabla["columna"], orientation="h", marker_color=estilo.AMARILLO,
            hovertemplate="%{y}: %{x:.2f} % vacío<extra></extra>",
        ))
        fig.update_layout(title=f"Columnas con nulos en {tabla}", xaxis_title="% de filas vacías",
                          height=120 + 38 * len(nulos_tabla))
        estilo.grafica(fig)

    st.markdown("**Qué se le hizo a esta tabla y por qué**")
    cambios = _cambios_de(tabla)
    if cambios.empty:
        st.caption("Esta tabla no se limpia: se arma directamente desde la configuración del proyecto.")
    else:
        st.dataframe(cambios, width="stretch", hide_index=True)

    # --- Nulos de todas las tablas -----------------------------------------------------------------
    st.subheader("Dónde faltan datos, en todas las tablas")
    todos = con_nulos.copy()
    todos["¿por qué?"] = [_motivo(t, c) for t, c in zip(todos["tabla"], todos["columna"])]
    minimo = st.slider("Mostrar columnas con más de este % de nulos", 0.0, 100.0, 0.0, 1.0, key="limpieza_minimo")
    todos = todos[todos["% nulos"] > minimo].sort_values("% nulos", ascending=False)
    st.dataframe(
        todos[["tabla", "columna", "nulos", "% nulos", "¿por qué?"]], width="stretch", hide_index=True,
        column_config={"% nulos": st.column_config.ProgressColumn("% nulos", min_value=0, max_value=100, format="%.2f %%")},
    )
    st.caption("El hueco más importante no es una casilla vacía sino una falta de meses: SIPSA no tiene precios "
               "entre enero de 2021 y enero de 2022. Está explicado en la pestaña «Calidad de datos».")

    # --- Todos los cambios -----------------------------------------------------------------------
    st.subheader("Todo lo que se modificó")
    todas = pd.DataFrame(txt.CAMBIOS, columns=["Fuente", "Dato", "Qué se modificó", "Por qué", "Con qué quedamos"])
    elegidas = st.multiselect("Filtrar por fuente", sorted(todas["Fuente"].unique()), key="limpieza_fuentes")
    if elegidas:
        todas = todas[todas["Fuente"].isin(elegidas)]
    st.dataframe(todas, width="stretch", hide_index=True)

    st.download_button(
        "Descargar el diccionario completo (CSV)",
        columnas.to_csv(index=False).encode("utf-8-sig"),
        file_name="diccionario_de_datos.csv", mime="text/csv",
    )
