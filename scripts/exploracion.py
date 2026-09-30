"""Exploracion de datos sobre la base integrada: las cinco etapas de clase.

1. Estructura       -> tabla de dimensiones y tipos por tabla
2. Faltantes/atipicos -> % de nulos por columna y boxplot de retornos
3. Calidad          -> completitud de SIPSA (dias con dato por mes)
4. Distribuciones   -> histograma de retornos logaritmicos
5. Correlaciones    -> precio vs clima (NASA POWER, IDEAM si esta), ENSO e insumos

Todo sale de data/processed/caso8.duckdb. Figuras en docs/figuras/ y cifras en
docs/exploracion.md. No interpreta: deja los numeros para que el equipo los lea.

Uso:
    python scripts/exploracion.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")  # sin ventana: corre igual en consola
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.rutas import BASE_DUCKDB, RAIZ
from src.indicators import vigilancia

FIGURAS = RAIZ / "docs" / "figuras"
SALIDA = RAIZ / "docs" / "exploracion.md"
HECHOS = ["fact_precio_mayorista", "fact_precio_productor", "fact_clima",
          "fact_comercio", "fact_produccion", "fact_insumos", "fact_enso"]


def _guardar(fig, nombre: str) -> str:
    fig.tight_layout()
    ruta = FIGURAS / nombre
    fig.savefig(ruta, dpi=160)
    plt.close(fig)
    return f"figuras/{nombre}"


def estructura(con) -> pd.DataFrame:
    filas = []
    for (tabla,) in con.execute(
        "SELECT table_name FROM duckdb_tables() WHERE table_name <> 'meta_actualizacion' ORDER BY 1"
    ).fetchall():
        tipos = con.execute(f"DESCRIBE {tabla}").fetchdf()
        filas.append({
            "tabla": tabla,
            "filas": con.execute(f"SELECT count(*) FROM {tabla}").fetchone()[0],
            "columnas": len(tipos),
            "numericas": int(tipos["column_type"].str.contains("INT|DOUBLE|DECIMAL|FLOAT").sum()),
            "texto": int((tipos["column_type"] == "VARCHAR").sum()),
        })
    return pd.DataFrame(filas)


def faltantes(con) -> tuple[pd.DataFrame, str]:
    filas = []
    for tabla in HECHOS:
        df = con.execute(f"SELECT * FROM {tabla}").fetchdf()
        for col, pct in (df.isna().mean() * 100).items():
            if pct > 0:
                filas.append({"tabla": tabla, "columna": col, "pct_nulos": round(pct, 2)})
    tabla = pd.DataFrame(filas).sort_values("pct_nulos", ascending=False)
    fig, ax = plt.subplots(figsize=(8, 0.35 * max(len(tabla), 4) + 1))
    etiquetas = tabla["tabla"].str.replace("fact_", "") + "." + tabla["columna"]
    ax.barh(etiquetas, tabla["pct_nulos"], color="#4C72B0")
    ax.invert_yaxis()
    ax.set_xlabel("% de valores nulos")
    ax.set_title("Valores faltantes por columna (solo columnas con nulos)")
    return tabla, _guardar(fig, "01_faltantes.png")


def retornos_nacionales(con) -> pd.DataFrame:
    """Mediana nacional por producto y mes y su retorno (calculo compartido con la app)."""
    return vigilancia.retornos_nacionales(con.execute("SELECT * FROM fact_precio_mayorista").fetchdf())


def huecos_sipsa(con) -> pd.DataFrame:
    """Meses sin ningun dato de SIPSA entre el primero y el ultimo publicado."""
    meses = con.execute("""
        SELECT DISTINCT periodo FROM fact_precio_mayorista ORDER BY periodo""").fetchdf()
    todos = pd.period_range(
        pd.Period(str(meses["periodo"].min()), "M"), pd.Period(str(meses["periodo"].max()), "M"), freq="M"
    )
    presentes = {pd.Period(str(p), "M") for p in meses["periodo"]}
    faltan = [p for p in todos if p not in presentes]
    return pd.DataFrame({"desde": [str(faltan[0])] if faltan else [], "hasta": [str(faltan[-1])] if faltan else [],
                         "meses_faltantes": [len(faltan)] if faltan else [], "meses_esperados": [len(todos)] if faltan else []})


def atipicos(ret: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Boxplot por producto y conteo de atipicos por la regla de Tukey (1,5 RIC)."""
    def contar(s):
        q1, q3 = s.quantile([0.25, 0.75])
        ric = q3 - q1
        return int(((s < q1 - 1.5 * ric) | (s > q3 + 1.5 * ric)).sum())

    r = ret.dropna(subset=["retorno"])
    resumen = (r.groupby("producto")["retorno"]
               .agg(n="count", desv="std", atipicos=contar)
               .sort_values("desv", ascending=False).round(4).reset_index())
    top = resumen.head(12)["producto"].tolist()
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.boxplot([r.loc[r["producto"] == p, "retorno"] for p in top], vert=False,
               tick_labels=top, flierprops={"markersize": 3})
    ax.axvline(0, color="grey", lw=0.8)
    ax.set_xlabel("Retorno logaritmico mensual del precio mayorista")
    ax.set_title("Los 12 productos mas volatiles (mediana nacional SIPSA)")
    return resumen, _guardar(fig, "02_boxplot_retornos.png")


def completitud(con) -> tuple[pd.DataFrame, str]:
    df = con.execute("SELECT dias_con_dato FROM fact_precio_mayorista").fetchdf()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(df["dias_con_dato"], bins=range(0, 33), color="#55A868", edgecolor="white")
    ax.set_xlabel("Dias con precio reportado en el mes")
    ax.set_ylabel("Series mercado-producto-mes")
    ax.set_title("Completitud de SIPSA")
    desc = df["dias_con_dato"].describe().round(1).to_frame("dias_con_dato").T
    desc["pct_meses_menos_10_dias"] = round((df["dias_con_dato"] < 10).mean() * 100, 2)
    return desc, _guardar(fig, "03_completitud_sipsa.png")


def distribucion(ret: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    r = ret["retorno"].dropna()
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.hist(r, bins=80, density=True, color="#C44E52", alpha=0.75, label="observado")
    x = np.linspace(r.min(), r.max(), 300)
    ax.plot(x, np.exp(-0.5 * ((x - r.mean()) / r.std()) ** 2) / (r.std() * np.sqrt(2 * np.pi)),
            color="black", lw=1, label="normal con la misma media y desviacion")
    ax.set_xlabel("Retorno logaritmico mensual")
    ax.set_title("Distribucion de los retornos de precio")
    ax.legend()
    stats = pd.DataFrame([{
        "n": len(r), "media": round(r.mean(), 4), "desv": round(r.std(), 4),
        "asimetria": round(r.skew(), 3), "curtosis_exceso": round(r.kurt(), 3),
        "pct_fuera_de_2_desv": round((abs(r - r.mean()) > 2 * r.std()).mean() * 100, 2),
    }])
    return stats, _guardar(fig, "04_histograma_retornos.png")


def correlaciones(con, ret: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """Correlacion de Spearman entre el retorno y la lluvia o el ONI de 0 a 3 meses antes.

    Spearman y no Pearson: los retornos tienen colas pesadas (ver curtosis) y
    Pearson se deja arrastrar por los meses extremos. El calculo vive en
    src/indicators/vigilancia.py, que tambien usa la app.
    """
    puente = con.execute("SELECT * FROM puente_zona_sipsa").fetchdf()
    clima = con.execute("SELECT * FROM fact_clima").fetchdf()
    enso = con.execute("SELECT anio * 100 + mes AS periodo, anomalia AS oni FROM fact_enso").fetchdf()

    lluvia = vigilancia.correlacion_lluvia(ret, clima, puente)
    # El ONI es uno solo para todo el pais: se correlaciona por producto y se
    # repite en cada zona de ese producto para la figura.
    zonas = puente.rename(columns={"producto_sipsa": "producto"})[["producto", "departamento"]]
    oni = vigilancia.correlacion_rezagada(ret, enso, [], "oni").merge(zonas, on="producto")
    tabla = pd.concat([lluvia, oni], ignore_index=True)
    tabla["variable"] = tabla["variable"].replace({"precipitacion_anomalia": "lluvia"})
    tabla = tabla.rename(columns={"rezago": "rezago_meses"})[
        ["producto", "departamento", "variable", "rezago_meses", "n", "spearman"]]
    if tabla.empty:
        return tabla, ""
    matriz = tabla.pivot_table(index=["producto", "departamento"],
                               columns=["variable", "rezago_meses"], values="spearman")
    fig, ax = plt.subplots(figsize=(3.5 + 0.8 * matriz.shape[1], 0.45 * len(matriz) + 2))
    im = ax.imshow(matriz.values, cmap="RdBu_r", vmin=-0.5, vmax=0.5, aspect="auto")
    ax.set_xticks(range(matriz.shape[1]), [f"{v}\nt-{r}" for v, r in matriz.columns], fontsize=7, rotation=45, ha="right")
    ax.set_yticks(range(len(matriz)), [f"{p} ({d})" for p, d in matriz.index], fontsize=8)
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            v = matriz.values[i, j]
            if not np.isnan(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=6)
    fig.colorbar(im, ax=ax, label="Spearman")
    ax.set_title("Retorno del precio vs clima y ENSO, con rezago")
    return tabla, _guardar(fig, "05_correlaciones.png")


def main() -> None:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(BASE_DUCKDB), read_only=True)
    ret = retornos_nacionales(con)

    est = estructura(con)
    falt, f1 = faltantes(con)
    atip, f2 = atipicos(ret)
    comp, f3 = completitud(con)
    huecos = huecos_sipsa(con)
    dist, f4 = distribucion(ret)
    corr, f5 = correlaciones(con, ret)
    con.close()

    fuertes = corr.loc[corr["spearman"].abs() >= 0.3] if not corr.empty else corr
    partes = [
        "# Exploracion de datos", "",
        "Generado por `scripts/exploracion.py` sobre `caso8.duckdb`. Solo cifras; la lectura la hace el equipo.", "",
        "## 1. Estructura", "", est.to_markdown(index=False), "",
        "## 2. Faltantes", "", f"![faltantes]({f1})", "", falt.to_markdown(index=False), "",
        "## 3. Atipicos (regla de Tukey sobre retornos mensuales)", "", f"![boxplot]({f2})", "",
        atip.to_markdown(index=False), "",
        "## 4. Calidad: completitud de SIPSA", "", f"![completitud]({f3})", "", comp.to_markdown(), "",
        "Meses sin ningun dato en el servicio web de SIPSA (todos los productos):", "",
        huecos.to_markdown(index=False) if not huecos.empty else "Ninguno.", "",
        "## 5. Distribucion de retornos", "", f"![histograma]({f4})", "", dist.to_markdown(index=False), "",
        "## 6. Correlaciones (Spearman, rezago 0-3 meses, n >= 24)", "",
        f"![correlaciones]({f5})" if f5 else "Sin pares suficientes.", "",
        f"Pares con |rho| >= 0,3: **{len(fuertes)}** de {len(corr)}.", "",
        fuertes.sort_values("spearman", key=abs, ascending=False).to_markdown(index=False)
        if not fuertes.empty else "", "",
    ]
    SALIDA.write_text("\n".join(partes), encoding="utf-8")
    print(f"listo: {SALIDA} y {len(list(FIGURAS.glob('*.png')))} figuras")


if __name__ == "__main__":
    main()
