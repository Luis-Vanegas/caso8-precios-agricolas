"""Figuras para explicar el modelo de pronostico (src/indicators/pronostico.py).

1. 06_pronostico_ejemplo.png: un alimento con su precio real, el backtest
   (lo que el modelo habria dicho cada mes sin ver el futuro) y el pronostico
   de los proximos 3 meses con su banda del 80 %.
2. 07_modelo_vs_ingenuo.png: error del modelo contra el del mejor ingenuo para
   cada alimento, y cuantos alimentos gana cada metodo en cada horizonte.

Lee la tabla resultado_pronostico_precio de data/processed/caso8.duckdb. Si la
base esta bloqueada (otra corrida la tiene abierta), arma el modelo en memoria
desde los parquet de data/interim y calcula el pronostico ahi mismo.

Uso:
    python scripts/figuras_modelo.py                    # elige el alimento donde el modelo gana por mas
    python scripts/figuras_modelo.py --producto Tomate
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")  # sin ventana: corre igual en consola
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.rutas import BASE_DUCKDB, RAIZ
from src.indicators import pronostico
from src.integration import modelo

FIGURAS = RAIZ / "docs" / "figuras"
TINTA, AZUL, GRIS, ROJO = "#1f2328", "#1f5fa8", "#8a8f98", "#c0392b"
MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]


def cargar() -> pd.DataFrame:
    try:
        con = duckdb.connect(str(BASE_DUCKDB), read_only=True)
        return con.execute("SELECT * FROM resultado_pronostico_precio").df()
    except duckdb.IOException:
        print("La base esta bloqueada: se arma el modelo en memoria desde data/interim.")
        con = duckdb.connect()
        modelo.construir(con)
        return pronostico.construir(con)


def _fecha(periodo: pd.Series) -> pd.Series:
    return pd.to_datetime(periodo.astype(int).astype(str), format="%Y%m")


def _mes_corto(valor, _pos=None) -> str:
    """Fecha del eje en espanol: 'sep 2026'."""
    fecha = mdates.num2date(valor)
    return f"{MESES[fecha.month - 1]} {fecha.year}"


def _pesos(valor, _pos=None) -> str:
    return f"${valor:,.0f}".replace(",", ".")


def elegir_producto(df: pd.DataFrame) -> str:
    """El alimento donde el modelo le gana por mas al ingenuo a 1 mes."""
    h1 = df[df["tipo"] == "pronostico"].query("horizonte == 1")
    ganadores = h1[h1["gana_al_ingenuo"]]
    base = ganadores if len(ganadores) else h1
    return base.assign(ventaja=base["mae_ingenuo"] - base["mae_modelo"]).nlargest(1, "ventaja")["producto"].iloc[0]


def figura_ejemplo(df: pd.DataFrame, producto: str) -> Path:
    d = df[df["producto"] == producto].copy()
    d["fecha"] = _fecha(d["periodo"])
    real = d[d["tipo"] == "real"].sort_values("fecha")
    prueba = d[d["tipo"] == "prueba"].sort_values("fecha")
    futuro = d[d["tipo"] == "pronostico"].sort_values("fecha")
    desde = prueba["fecha"].min() - pd.DateOffset(months=12)
    real = real[real["fecha"] >= desde]
    hoy = real.iloc[-1]

    fig, ax = plt.subplots(figsize=(11, 5.4))
    ax.plot(real["fecha"], real["valor"], color=TINTA, lw=2.2, label="Precio real (mediana nacional)")
    ax.plot(prueba["fecha"], prueba["valor"], color=AZUL, lw=1.4, ls=":", marker="o", ms=4,
            label="Prueba: lo que el modelo habría dicho un mes antes, sin ver el futuro")
    # El pronostico arranca en el ultimo dato real para que la linea no quede suelta.
    x = pd.concat([pd.Series([hoy["fecha"]]), futuro["fecha"]])
    y = pd.concat([pd.Series([hoy["valor"]]), futuro["valor"]])
    ax.plot(x, y, color=AZUL, lw=2.2, ls="--", label="Pronóstico de los próximos 3 meses")
    ax.fill_between(x, pd.concat([pd.Series([hoy["valor"]]), futuro["lim_inf"]]),
                    pd.concat([pd.Series([hoy["valor"]]), futuro["lim_sup"]]),
                    color=AZUL, alpha=0.15, label="Banda del 80 % (sale de los errores reales de la prueba)")
    ax.axvline(hoy["fecha"], color=GRIS, lw=1, ls=(0, (2, 3)))
    ax.text(hoy["fecha"], ax.get_ylim()[1], "  hoy", color=GRIS, va="top")

    v = futuro.iloc[0]
    metodo = {"regresion": "la regresión", "sin_cambio": "el ingenuo «sin cambio»",
              "estacional": "el ingenuo «estacional»"}[v["modelo"]]
    ax.set_title(f"{producto}: el modelo puesto a prueba y su pronóstico", loc="left", fontsize=14,
                 weight="bold", pad=26)
    ax.xaxis.set_major_formatter(FuncFormatter(_mes_corto))
    coma = lambda x: f"{x:.1f}".replace(".", ",")  # noqa: E731  decimal con coma, como se escribe en Colombia
    ax.text(0, 1.02, f"Error típico a 1 mes: modelo {coma(v['mae_modelo'])} %  ·  mejor ingenuo "
            f"{coma(v['mae_ingenuo'])} %  →  se usa {metodo}", transform=ax.transAxes, color=GRIS, fontsize=10, va="bottom")
    ax.yaxis.set_major_formatter(_pesos)
    ax.set_ylabel("Pesos por kilo")
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e5e5e5")
    ax.legend(loc="upper left", fontsize=9, frameon=False)
    fig.tight_layout()
    ruta = FIGURAS / "06_pronostico_ejemplo.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


def figura_comparacion(df: pd.DataFrame) -> Path:
    fut = df[df["tipo"] == "pronostico"]
    h1 = fut[fut["horizonte"] == 1]

    fig, (izq, der) = plt.subplots(1, 2, figsize=(12, 5.4), gridspec_kw={"width_ratios": [1.15, 1]})
    color = h1["gana_al_ingenuo"].map({True: AZUL, False: GRIS})
    izq.scatter(h1["mae_ingenuo"], h1["mae_modelo"], c=color, s=40, zorder=3)
    tope = max(h1["mae_ingenuo"].max(), h1["mae_modelo"].max()) * 1.08
    izq.plot([0, tope], [0, tope], color=TINTA, lw=1)
    izq.plot([0, tope], [0, tope * pronostico.MARGEN_PARA_GANAR], color=AZUL, lw=1, ls="--")
    izq.text(tope * 0.98, tope * 0.84, "debajo de la línea punteada:\nel modelo gana (5 % menos error)",
             ha="right", color=AZUL, fontsize=9)
    izq.set_xlim(0, tope)
    izq.set_ylim(0, tope)
    izq.set_xlabel("Error del mejor ingenuo (%)")
    izq.set_ylabel("Error del modelo (%)")
    izq.set_title("Cada punto es un alimento (pronóstico a 1 mes)", loc="left", fontsize=11, weight="bold")
    izq.spines[["top", "right"]].set_visible(False)

    conteo = (fut.astype({"horizonte": int}).groupby(["horizonte", "modelo"]).size().unstack(fill_value=0)
              .reindex(columns=["regresion", "estacional", "sin_cambio"], fill_value=0))
    nombres = {"regresion": "Regresión (el modelo)", "estacional": "Ingenuo estacional",
               "sin_cambio": "Ingenuo «sin cambio»"}
    colores = {"regresion": AZUL, "estacional": "#d4a017", "sin_cambio": GRIS}
    abajo = pd.Series(0, index=conteo.index)
    for col in conteo.columns:
        der.bar(conteo.index, conteo[col], bottom=abajo, color=colores[col], label=nombres[col], width=0.6)
        for h, n in conteo[col].items():
            if n:
                der.text(h, abajo[h] + n / 2, str(n), ha="center", va="center", color="white", fontsize=10, weight="bold")
        abajo += conteo[col]
    der.set_xticks(conteo.index, [f"{h} mes" + ("es" if h > 1 else "") for h in conteo.index])
    der.set_ylabel("Alimentos")
    der.set_title("Qué método se usa en cada horizonte", loc="left", fontsize=11, weight="bold")
    der.legend(fontsize=9, frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3)
    der.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    ruta = FIGURAS / "07_modelo_vs_ingenuo.png"
    fig.savefig(ruta, dpi=150)
    plt.close(fig)
    return ruta


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--producto", help="alimento a graficar (por defecto, donde el modelo gana por mas)")
    args = parser.parse_args(argv)
    df = cargar()
    producto = args.producto or elegir_producto(df)
    FIGURAS.mkdir(parents=True, exist_ok=True)
    print(figura_ejemplo(df, producto))
    print(figura_comparacion(df))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
