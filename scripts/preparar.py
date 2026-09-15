"""Fase 2: limpia lo descargado, lo perfila y deja los CSV para OpenRefine.

Escribe cada tabla dos veces en data/interim/:
  - `.parquet` para el pipeline (tipado, comprimido)
  - `.csv` en UTF-8 para OpenRefine y Power Query

El reporte de perfilado sale por pantalla y queda en docs/perfilado.md.

Uso:
    python scripts/preparar.py
    python scripts/preparar.py --solo sipsa
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cleaning import complementarias, faostat, homologacion
from src.cleaning import sipsa as limpieza_sipsa
from src.common.rutas import RAIZ, carpeta_intermedia
from src.profiling.perfil import (
    comercio_imposible,
    duplicados,
    huecos_de_serie,
    negativos,
    perfilar,
)

log = logging.getLogger("preparar")

REPORTE = RAIZ / "docs" / "perfilado.md"

# Claves que deberian identificar una fila de forma unica en cada tabla.
CLAVES = {
    "faostat_pp": ["item_codigo", "elemento_codigo", "anio", "mes_codigo"],
    "faostat_qcl": ["item_codigo", "elemento_codigo", "anio"],
    "faostat_tcl": ["item_codigo", "elemento_codigo", "anio"],
    "faostat_fbs": ["item_codigo", "elemento_codigo", "anio"],
    "faostat_qv": ["item_codigo", "elemento_codigo", "anio"],
    "faostat_pe": ["elemento_codigo", "anio", "mes_codigo"],
    "sipsa_diario": ["registro_id"],
    "sipsa_mensual": ["mercado", "producto", "anio", "mes"],
    "clima": ["producto", "departamento", "anio", "mes"],
    "enso": ["anio", "trimestre"],
    "insumos": ["commodity", "anio", "mes"],
    "zonas_puente": ["producto_sipsa", "producto_zona", "departamento"],
}


def construir() -> dict[str, pd.DataFrame]:
    """Arma todas las tablas limpias. Cada fuente falla por separado."""
    tablas: dict[str, pd.DataFrame] = {}

    for dominio in faostat.ZIPS:
        try:
            tablas[f"faostat_{dominio.lower()}"] = faostat.extraer_colombia(dominio)
        except Exception as exc:
            log.error("FAOSTAT %s: %s: %s", dominio, type(exc).__name__, exc)

    try:
        diario = limpieza_sipsa.limpiar()
        tablas["sipsa_diario"] = diario
        mensual = limpieza_sipsa.a_mensual(diario)
        # La homologacion se pega aca: sin la columna del item de FAO, Power
        # Query no tiene por donde cruzar SIPSA con FAOSTAT.
        mapeo = homologacion.cargar()
        tablas["sipsa_mensual"] = mensual.merge(
            mapeo, left_on="producto", right_on="producto_sipsa", how="left"
        ).drop(columns=["producto_sipsa"])
        # Se valida aca y no en el reporte para que corra siempre, incluso con --solo.
        for problema in homologacion.validar(
            mapeo,
            set(mensual["producto"]),
            set(tablas.get("faostat_qcl", pd.DataFrame({"item_codigo": []}))["item_codigo"]),
        ):
            log.error("homologacion: %s", problema)
    except Exception as exc:
        log.error("SIPSA: %s: %s", type(exc).__name__, exc)

    for nombre, funcion in (
        ("clima", lambda: complementarias.anomalia_precipitacion(complementarias.limpiar_clima())),
        ("enso", complementarias.limpiar_enso),
        ("insumos", complementarias.limpiar_insumos),
        ("zonas_puente", complementarias.puente_zona_sipsa),
    ):
        try:
            tablas[nombre] = funcion()
        except Exception as exc:
            log.error("%s: %s: %s", nombre, type(exc).__name__, exc)

    return tablas


def exportar(tablas: dict[str, pd.DataFrame]) -> list[str]:
    """Escribe parquet y CSV. El CSV va en UTF-8 con BOM para que Excel lo abra bien."""
    escritos = []
    for nombre, df in tablas.items():
        if df.empty:
            log.warning("%s quedo vacia, no se exporta", nombre)
            continue
        destino = carpeta_intermedia(nombre.split("_")[0])
        df.to_parquet(destino / f"{nombre}.parquet", index=False)
        df.to_csv(destino / f"{nombre}.csv", index=False, encoding="utf-8-sig")
        escritos.append(f"{nombre}: {len(df):,} filas")
    return escritos


def reportar(tablas: dict[str, pd.DataFrame]) -> str:
    """Arma el reporte de perfilado en markdown."""
    partes = [
        "# Perfilado de las tablas limpias",
        "",
        "Generado por `scripts/preparar.py`. Una fila por columna de cada tabla.",
        "",
        "## Resumen por tabla",
        "",
        "| tabla | filas | columnas | duplicados por clave |",
        "|---|---:|---:|---:|",
    ]
    for nombre, df in tablas.items():
        dup = duplicados(df, CLAVES.get(nombre, []))
        partes.append(f"| {nombre} | {len(df):,} | {len(df.columns)} | {dup:,} |")

    partes += ["", "## Columnas", ""]
    perfiles = pd.concat(
        [perfilar(df, nombre) for nombre, df in tablas.items() if not df.empty],
        ignore_index=True,
    )
    partes.append(perfiles.to_markdown(index=False))

    partes += ["", "## Homologacion SIPSA - FAOSTAT", ""]
    mapeo = homologacion.cargar()
    problemas = homologacion.validar(
        mapeo,
        set(tablas["sipsa_mensual"]["producto"]) if "sipsa_mensual" in tablas else set(),
        set(tablas["faostat_qcl"]["item_codigo"]) if "faostat_qcl" in tablas else set(),
    )
    if problemas:
        partes.append("**Problemas detectados:**")
        partes += [f"- {p}" for p in problemas]
    else:
        partes.append("Mapeo validado sin problemas contra los datos reales.")
    partes += ["", homologacion.resumen(mapeo).to_markdown(index=False), ""]
    choques = homologacion.colisiones(mapeo)
    if not choques.empty:
        partes += [
            "Items de FAO que reciben mas de un producto de SIPSA. En estos casos el precio "
            "productor de FAO no corresponde a ningun producto de SIPSA por separado:",
            "",
            choques.to_markdown(index=False),
        ]

    partes += ["", "## Inconsistencias", ""]

    for nombre, columna in (("faostat_pp", "valor"), ("sipsa_diario", "precio_cop_kg")):
        if nombre in tablas:
            partes.append(f"- Negativos en `{nombre}.{columna}`: **{negativos(tablas[nombre], columna)}**")

    if "faostat_tcl" in tablas and "faostat_qcl" in tablas:
        imposibles = comercio_imposible(tablas["faostat_tcl"], tablas["faostat_qcl"])
        # Produccion en cero para un item que si produce en otros anios no es una
        # inconsistencia: es un anio que la fuente todavia no publico.
        sin_produccion = imposibles[imposibles["producido"] == 0]
        reales = imposibles[imposibles["producido"] > 0]
        partes.append(
            f"- Item-anio con exportaciones mayores a produccion mas importaciones: "
            f"**{len(imposibles):,}** (en toneladas, solo items comparables). De esos, "
            f"**{len(reales):,}** tienen produccion registrada y son inconsistencias a explicar "
            f"(reexportacion o stock del anio anterior); los otros **{len(sin_produccion):,}** "
            f"tienen produccion en cero, o sea que a la fuente le falta publicar ese anio."
        )
        partes.append(
            f"- Excluidos por no ser comparables: **{imposibles.attrs['items_no_comparables']:,}** "
            f"items de comercio sin produccion primaria (agregados de grupo y productos "
            f"procesados), equivalentes a {imposibles.attrs['no_comparables']:,} item-anio."
        )
        if not reales.empty:
            partes += [
                "",
                "Las diez inconsistencias reales mas grandes:",
                "",
                reales.head(10).to_markdown(index=False),
            ]

    if "faostat_pp" in tablas:
        anual = tablas["faostat_pp"].query("frecuencia == 'anual'")
        huecos = huecos_de_serie(anual, ["item", "elemento"], "anio")
        con_hueco = len(huecos)
        largos = int((huecos["hueco_mayor"] > 3).sum()) if not huecos.empty else 0
        partes.append(
            f"- Series anuales de precios con huecos: **{con_hueco:,}**, "
            f"de las cuales **{largos:,}** tienen un hueco de mas de 3 anios "
            f"(no se interpolan, se dejan vacias)."
        )

    return "\n".join(partes) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solo", help="prefijo de tabla a procesar (faostat, sipsa, clima...)")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    tablas = construir()
    if args.solo:
        tablas = {n: d for n, d in tablas.items() if n.startswith(args.solo)}
        if not tablas:
            print(f"ninguna tabla empieza con '{args.solo}'")
            return 1

    print("\n--- exportado a data/interim ---")
    for linea in exportar(tablas):
        print(" ", linea)

    if args.solo:
        # Una corrida parcial no debe pisar el reporte general con media foto.
        print("\n(corrida parcial: no se reescribe docs/perfilado.md)")
    else:
        REPORTE.write_text(reportar(tablas), encoding="utf-8")
        print(f"\nReporte de perfilado: {REPORTE.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
