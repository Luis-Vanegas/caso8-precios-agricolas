"""Portada: que esta pasando este mes, en una sola pantalla."""

import numpy as np
import streamlit as st

import estilo
import graficas
from datos import con_indicadores, enso, fecha, frescura, mercados_geo, tabla_existe, ultimo_mes_cerrado

estilo.aplicar()
estilo.encabezado(
    "¿Qué alimento se está disparando?",
    "Vigilamos 33 productos en 20 mercados mayoristas de Colombia y avisamos cuando un "
    "precio se mueve de forma anormal para ese producto en ese mercado.",
)

df = con_indicadores()
mes = ultimo_mes_cerrado()
datos_mes = df[df["periodo"] == mes]
en_curso = int(df["periodo"].max())

estilo.chips([f"Último mes cerrado: {fecha(mes)}"]
             + ([f"{fecha(en_curso)} en curso: datos parciales"] if en_curso > mes else []))

# --- Numeros grandes -----------------------------------------------------------
fase = enso().iloc[-1]
estilo.contadores([
    ("series producto-mercado vigiladas", len(datos_mes), "", estilo.TINTA),
    ("alertas rojas (más de 3 desviaciones)", int((datos_mes["alerta"] == "roja").sum()), "", estilo.ROJO),
    ("alertas amarillas (entre 2 y 3)", int((datos_mes["alerta"] == "amarilla").sum()), "", "#B38A12"),
    (f"índice ONI · {estilo.fase_legible(fase['fase'])}", round(float(fase["anomalia"]), 2), "°C", estilo.AZUL),
])

# --- Alertas y mapa --------------------------------------------------------------
izq, der = st.columns([1, 1.4], gap="large")

with izq:
    st.subheader(f"Alertas de {fecha(mes)}")
    encendidas = datos_mes[datos_mes["alerta"].isin(["roja", "amarilla"])]
    encendidas = encendidas.reindex(encendidas["z_score"].abs().sort_values(ascending=False).index)
    if encendidas.empty:
        st.success("Ningún precio se movió de forma anormal este mes.")
    else:
        tarjetas = []
        for i, f in enumerate(encendidas.head(8).itertuples()):
            cambio = np.exp(f.retorno_log) - 1          # retorno logaritmico -> % normal
            flecha = "▲" if cambio > 0 else "▼"
            tarjetas.append(estilo.tarjeta(
                titulo=f.producto.replace("*", ""),
                dato=f"{flecha} {cambio:+.0%}",
                nota=f"{f.mercado.title()} · {estilo.pesos(f.precio_cop_kg)}/kg · z = {f.z_score:+.1f}",
                color=estilo.COLOR_ALERTA[f.alerta], late=f.alerta == "roja", retraso=min(i, 4),
            ))
        estilo.fila_de_tarjetas(tarjetas, ancho_minimo=210)
        if len(encendidas) > 8:
            st.caption(f"Y {len(encendidas) - 8} más en el Semáforo de alertas.")

with der:
    estilo.grafica(graficas.mapa_mercados(datos_mes, mercados_geo(), "Mercados con alertas"))
    st.caption("Cada punto es un mercado. Rojo o amarillo = tiene alertas (la más grave manda el color); "
               "cuanto más grande, más productos con alerta. Pasa el mouse para ver cuáles.")

# --- El Nino -----------------------------------------------------------------------
if fase["anomalia"] >= 0.5:
    estilo.explicacion(
        f"El Pacífico está <b>{fase['anomalia']:+.2f} °C</b> más caliente de lo normal "
        f"({fase['trimestre']} {int(fase['anio'])}): hay <b>El Niño</b>. En Colombia, un choque "
        "fuerte de El Niño sube la inflación de alimentos a los <b>4 y 5 meses</b> "
        "(Abril-Salcedo et al., 2016). Por eso conviene vigilar con más cuidado los próximos meses.",
        etiqueta="Ojo con el clima",
    )

# --- Fuentes ------------------------------------------------------------------------
st.subheader("Seis fuentes, una sola base")
fuentes = [
    ("SIPSA · DANE", "Diario", "Precios mayoristas: aquí nace la alerta"),
    ("IDEAM", "Cada 10 min" if tabla_existe("fact_sensor_ideam") else "Cada 10 min · por cargar",
     "Lluvia medida por sensores en las zonas productoras"),
    ("FAOSTAT · FAO", "Anual", "Producción, comercio e importaciones"),
    ("NASA POWER", "Mensual", "Clima histórico por zona productora"),
    ("ONI · NOAA", "Mensual", "El Niño y La Niña"),
    ("Pink Sheet · Banco Mundial", "Mensual", "Precios de fertilizantes y energía"),
]
estilo.fila_de_tarjetas(
    [estilo.tarjeta(n, f, d, retraso=i % 4) for i, (n, f, d) in enumerate(fuentes)], ancho_minimo=260
)

with st.expander("¿Qué tan frescos están los datos?"):
    st.dataframe(frescura(), width="stretch", hide_index=True)
    st.caption("La app lee la base DuckDB; no llama a las APIs en vivo. Si una fuente se cae, la app sigue funcionando.")

estilo.pie()
