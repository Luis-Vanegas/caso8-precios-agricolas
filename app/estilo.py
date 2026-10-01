"""Estilo visual de la app: colores, letras, animaciones y piezas reutilizables.

Todo lo visual vive en este archivo para que las paginas solo se ocupen de los
datos. Si quieren cambiar un color, se cambia aca y cambia en toda la app.

Como se usa en una pagina:

    import estilo
    estilo.aplicar()                       # siempre de primero
    estilo.encabezado("Titulo", "Subtitulo")
    estilo.explicacion("Esto se lee asi...")
"""

from __future__ import annotations

import html

import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st
import streamlit.components.v1 as components

# --- 1. Paleta ---------------------------------------------------------------
# Inspirada en el campo colombiano y en la bandera, pero en tonos sobrios para
# que se lea bien proyectada en un auditorio.

VERDE = "#1B5E3B"      # cafetal: color principal
AMARILLO = "#E9B824"   # maiz / bandera: alertas amarillas y acentos
AZUL = "#1D4E89"       # bandera: datos neutros y La Nina
ROJO = "#C0392B"       # bandera: alertas rojas y El Nino
TIERRA = "#8A5A2B"     # suelo: series secundarias
PAPEL = "#FAF7F0"      # fondo general
TINTA = "#1C2521"      # texto principal
GRIS = "#6B7065"       # texto secundario
BORDE = "#E6E0D2"      # lineas suaves

# Colores del semaforo, en un solo diccionario para no repetirlos.
COLOR_ALERTA = {"roja": ROJO, "amarilla": AMARILLO, "verde": VERDE}

# Orden de colores cuando una grafica tiene varias series.
SERIES = [VERDE, AZUL, AMARILLO, ROJO, TIERRA, "#4F7C8A"]


# --- 2. CSS -----------------------------------------------------------------
# CSS es el lenguaje que le dice al navegador como se ve cada cosa. Streamlit
# nos deja inyectarlo con st.html. Cada bloque lleva un comentario.

_CSS = f"""
<style>
/* Letras: Fraunces (titulos, con serifa), Inter (texto), JetBrains Mono (numeros) */
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@500&display=swap');

/* Solo texto: si se cambia la letra de todo, se rompen los iconos del menu */
.stApp p, .stApp li, .stApp label, .stApp input, .stMarkdown, [data-testid="stCaptionContainer"] {{
  font-family: 'Inter', sans-serif; }}
.simple, .tarjeta, .subtitulo, .chip {{ font-family: 'Inter', sans-serif; }}
h1, h2, h3 {{ font-family: 'Fraunces', serif !important; color: {TINTA}; letter-spacing: -0.01em; }}
h1 {{ font-weight: 700 !important; }}

/* Para proyector: subtitulos con aire arriba y textos de apoyo mas legibles */
h2, h3 {{ margin-top: 1.4rem !important; }}
[data-testid="stCaptionContainer"] {{ font-size: .95rem; }}
.simple {{ font-size: 1rem; line-height: 1.5; }}

/* Fondo tipo papel y ancho de lectura comodo */
.stApp {{ background: {PAPEL}; }}
.block-container {{ padding-top: 2.2rem; max-width: 1280px; }}

/* Barra lateral */
[data-testid="stSidebar"] {{ background: #F1ECDF; border-right: 1px solid {BORDE}; }}

/* Franja tricolor arriba de cada pagina (proporcion de la bandera: 2-1-1) */
.franja {{ height: 6px; border-radius: 3px; margin-bottom: 1.2rem;
  background: linear-gradient(90deg, {AMARILLO} 0 50%, {AZUL} 50% 75%, {ROJO} 75% 100%); }}

.antetitulo {{ text-transform: uppercase; letter-spacing: .12em; font-size: .75rem;
  color: {VERDE}; font-weight: 600; margin-bottom: .2rem; }}
.subtitulo {{ color: {GRIS}; font-size: 1.05rem; max-width: 60rem; margin-top: -.4rem; }}

/* Animacion de entrada: cada bloque aparece subiendo un poco */
@keyframes subir {{ from {{ opacity: 0; transform: translateY(12px); }}
                   to   {{ opacity: 1; transform: none; }} }}
.anim {{ animation: subir .6s ease-out both; }}
.anim-1 {{ animation-delay: .08s; }} .anim-2 {{ animation-delay: .16s; }}
.anim-3 {{ animation-delay: .24s; }} .anim-4 {{ animation-delay: .32s; }}

/* Tarjetas */
.tarjeta {{ background: #fff; border: 1px solid {BORDE}; border-radius: 14px;
  padding: 1rem 1.1rem; box-shadow: 0 1px 2px rgba(0,0,0,.04); height: 100%; }}
.tarjeta h4 {{ font-family: 'Fraunces', serif; margin: 0 0 .25rem 0; font-size: 1.05rem; color: {TINTA}; }}
.tarjeta .dato {{ font-family: 'JetBrains Mono', monospace; font-size: 1.35rem; color: {TINTA}; }}
.tarjeta .nota {{ color: {GRIS}; font-size: .85rem; }}

/* Tarjeta de alerta con borde del color del semaforo */
.alerta {{ border-left: 6px solid var(--c); }}

/* Punto que late en las alertas rojas */
@keyframes latido {{ 0% {{ box-shadow: 0 0 0 0 rgba(192,57,43,.55); }}
                     70% {{ box-shadow: 0 0 0 10px rgba(192,57,43,0); }}
                     100% {{ box-shadow: 0 0 0 0 rgba(192,57,43,0); }} }}
.punto {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%;
  background: var(--c); margin-right: .45rem; vertical-align: middle; }}
.punto.late {{ animation: latido 1.8s infinite; }}

/* Recuadro "En palabras simples" */
.simple {{ background: #EEF4EF; border: 1px solid #CFE0D3; border-radius: 12px;
  padding: .85rem 1rem; margin: .4rem 0 1rem 0; }}
.simple b.etiqueta {{ color: {VERDE}; text-transform: uppercase; font-size: .72rem;
  letter-spacing: .1em; display: block; margin-bottom: .2rem; }}

/* Etiquetas pequenas (fuente, herramienta, estado) */
.chip {{ display: inline-block; padding: .12rem .6rem; border-radius: 999px; font-size: .78rem;
  background: #fff; border: 1px solid {BORDE}; margin: 0 .3rem .3rem 0; color: {TINTA}; }}
.chip.parcial {{ background: #FFF6DA; border-color: {AMARILLO}; }}

/* Numero grande de cada paso del recorrido */
.paso {{ display: flex; gap: 1rem; align-items: center; margin: 2.2rem 0 .6rem 0; }}
.paso .n {{ font-family: 'Fraunces', serif; font-size: 2.4rem; color: #fff; background: {VERDE};
  width: 3.2rem; height: 3.2rem; border-radius: 50%; display: grid; place-items: center; flex: none; }}
.paso .t {{ font-family: 'Fraunces', serif; font-size: 1.6rem; color: {TINTA}; line-height: 1.1; }}
.paso .h {{ color: {GRIS}; font-size: .9rem; }}

/* Tablas y metricas nativas de Streamlit un poco mas limpias */
[data-testid="stMetricValue"] {{ font-family: 'JetBrains Mono', monospace; }}
[data-testid="stDataFrame"] {{ border: 1px solid {BORDE}; border-radius: 10px; }}
</style>
"""


def aplicar() -> None:
    """Inyecta el CSS y la plantilla de graficas. Va al comienzo de cada pagina."""
    st.html(_CSS)
    pio.templates.default = "caso8"


# --- 3. Plantilla de graficas (Plotly) ----------------------------------------
# Una "plantilla" es un estilo que Plotly aplica a todas las graficas: fondo,
# letra, colores. Se registra una vez y se usa en todas.

pio.templates["caso8"] = go.layout.Template(
    layout=go.Layout(
        font=dict(family="Inter, sans-serif", color=TINTA, size=13),
        # Titulo pegado a la izquierda: centrado se cortaba en las columnas angostas.
        title=dict(font=dict(family="Fraunces, serif", size=16), x=0, xanchor="left",
                   xref="container", pad=dict(l=4)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        colorway=SERIES,
        xaxis=dict(gridcolor="#EFEAE0", linecolor=BORDE, zeroline=False, automargin=True),
        yaxis=dict(gridcolor="#EFEAE0", linecolor=BORDE, zeroline=False, automargin=True),
        legend=dict(orientation="h", y=-0.18, x=0),
        margin=dict(l=10, r=10, t=50, b=10),
        hoverlabel=dict(font_family="Inter, sans-serif"),
        separators=",.",  # formato colombiano: coma decimal, punto de miles
    )
)


# --- 4. Piezas reutilizables ---------------------------------------------------

def encabezado(titulo: str, subtitulo: str = "", antetitulo: str = "Caso 8 · Precios agrícolas") -> None:
    """Franja tricolor + antetitulo + titulo grande + subtitulo gris."""
    st.html(
        f"""
        <div class="anim">
          <div class="franja"></div>
          <div class="antetitulo">{html.escape(antetitulo)}</div>
          <h1 style="margin:0 0 .6rem 0; font-size:2.4rem;">{html.escape(titulo)}</h1>
          <p class="subtitulo">{html.escape(subtitulo)}</p>
        </div>
        """
    )


def explicacion(texto_html: str, etiqueta: str = "En palabras simples") -> None:
    """Recuadro verde claro para explicar algo sin tecnicismos.

    Acepta HTML sencillo (<b>, <i>, <br>) para resaltar palabras.
    """
    st.html(f'<div class="simple anim"><b class="etiqueta">{etiqueta}</b>{texto_html}</div>')


def chips(textos: list[str], clase: str = "") -> None:
    """Fila de etiquetas pequenas, por ejemplo las herramientas de un paso."""
    st.html("".join(f'<span class="chip {clase}">{html.escape(t)}</span>' for t in textos))


def paso(numero: int, titulo: str, herramienta: str) -> None:
    """Encabezado numerado de cada paso del recorrido."""
    st.html(
        f"""
        <div class="paso anim">
          <div class="n">{numero}</div>
          <div><div class="t">{html.escape(titulo)}</div>
               <div class="h">Herramienta: {html.escape(herramienta)}</div></div>
        </div>
        """
    )


def tarjeta(titulo: str, dato: str, nota: str = "", color: str | None = None, late: bool = False,
            retraso: int = 0) -> str:
    """Devuelve el HTML de una tarjeta. Se devuelve texto (no se pinta) para poder
    armar varias en una misma fila con `fila_de_tarjetas`."""
    punto = ""
    borde = ""
    if color:
        punto = f'<span class="punto {"late" if late else ""}" style="--c:{color}"></span>'
        borde = f' alerta" style="--c:{color}'
    return (
        f'<div class="tarjeta anim anim-{retraso}{borde}">'
        f"<h4>{punto}{html.escape(titulo)}</h4>"
        f'<div class="dato">{html.escape(dato)}</div>'
        f'<div class="nota">{html.escape(nota)}</div></div>'
    )


def fila_de_tarjetas(tarjetas: list[str], ancho_minimo: int = 220) -> None:
    """Pinta las tarjetas en una grilla que se acomoda sola al ancho disponible:
    caben tantas columnas como tarjetas de `ancho_minimo` pixeles."""
    st.html(
        f'<div style="display:grid; gap:.8rem; '
        f'grid-template-columns:repeat(auto-fill, minmax({ancho_minimo}px, 1fr));">'
        + "".join(tarjetas)
        + "</div>"
    )


def contadores(items: list[tuple[str, float, str, str]]) -> None:
    """Fila de numeros grandes que cuentan desde 0 hasta su valor al cargar.

    items = [(etiqueta, valor, sufijo, color), ...]

    Usa un pedacito de JavaScript, por eso va en `components.html` (un marco
    aparte): st.html no ejecuta scripts.
    """
    celdas = "".join(
        f"""<div class="k"><div class="v" data-fin="{valor}" data-dec="{1 if valor % 1 else 0}"
             style="color:{color}">0</div><div class="s">{html.escape(sufijo)}</div>
             <div class="e">{html.escape(etiqueta)}</div></div>"""
        for etiqueta, valor, sufijo, color in items
    )
    components.html(
        f"""
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@500&family=JetBrains+Mono:wght@500&display=swap" rel="stylesheet">
        <style>
          body {{ margin:0; font-family:Inter, sans-serif; background:transparent; }}
          .fila {{ display:grid; grid-template-columns:repeat({len(items)}, 1fr); gap:12px; }}
          .k {{ background:#fff; border:1px solid {BORDE}; border-radius:14px; padding:14px 16px; }}
          .v {{ font-family:'JetBrains Mono', monospace; font-size:34px; line-height:1; display:inline; }}
          .s {{ display:inline; font-family:'JetBrains Mono', monospace; font-size:16px; color:{GRIS}; margin-left:4px; }}
          .e {{ color:{GRIS}; font-size:13px; margin-top:6px; }}
        </style>
        <div class="fila">{celdas}</div>
        <script>
          // Cuenta de 0 al valor final en ~1 segundo, frenando al final.
          document.querySelectorAll('.v').forEach(el => {{
            const fin = parseFloat(el.dataset.fin), dec = parseInt(el.dataset.dec);
            const t0 = performance.now(), dur = 1100;
            const paso = t => {{
              const p = Math.min(1, (t - t0) / dur), suave = 1 - Math.pow(1 - p, 3);
              el.textContent = (fin * suave).toLocaleString('es-CO',
                {{minimumFractionDigits: dec, maximumFractionDigits: dec}});
              if (p < 1) requestAnimationFrame(paso);
            }};
            requestAnimationFrame(paso);
          }});
        </script>
        """,
        height=112,
    )


def pesos(valor: float) -> str:
    """1996.4 -> '$1.996'. Formato colombiano: punto para los miles."""
    return "$" + f"{valor:,.0f}".replace(",", ".")


def fase_legible(fase: str) -> str:
    """Los datos de NOAA dicen 'El Nino'; en pantalla va con tilde."""
    return {"El Nino": "El Niño", "La Nina": "La Niña"}.get(fase, fase)


def grafica(fig) -> None:
    """Pinta una figura de Plotly con NUESTRO estilo (theme=None evita que
    Streamlit le ponga el suyo encima)."""
    st.plotly_chart(fig, width="stretch", theme=None,
                    config={"displaylogo": False, "locale": "es"})


def pie() -> None:
    """Nota final de cada pagina."""
    st.caption(
        "Proyecto académico · Adquisición e Integración de Datos · Ingeniería en Ciencia de Datos, ITM. "
        "Los umbrales de alerta son convenciones de este trabajo, no estándares oficiales."
    )
