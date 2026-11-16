"""Exporta a JSON lo que muestra la web (carpeta web/).

La web es estatica: no consulta la base, lee archivos JSON. Este script los
escribe en web/public/datos/ a partir de la base y de los mismos calculos que
usa el resto del proyecto (src/indicators). Correr despues de integrar.py:

    python scripts/exportar_web.py
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.common.rutas import BASE_DUCKDB, RAIZ
from src.indicators import vigilancia, volatilidad

SALIDA = RAIZ / "web" / "public" / "datos"
MESES_DE_HISTORIA = 24      # cuantos meses hacia atras lleva cada serie
NACIONAL = "Nacional"
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]


def nombre_mes(periodo: int) -> str:
    """202609 -> 'septiembre de 2026'."""
    return f"{MESES[periodo % 100 - 1]} de {periodo // 100}"


def nombre_producto(producto: str) -> str:
    """Quita el asterisco con que el DANE marca algunos productos."""
    return producto.replace("*", "").strip()


def nombre_mercado(mercado: str) -> str:
    """'SAN JOSÉ DE CÚCUTA' -> 'San José de Cúcuta'."""
    return mercado.title().replace(" De ", " de ").replace("D.c.", "D.C.")


def _sumar_meses(periodo: int, meses: int) -> int:
    n = periodo // 100 * 12 + periodo % 100 - 1 + meses
    return n // 12 * 100 + n % 12 + 1


def _numero(valor, decimales: int = 1):
    """Numero redondeado, o None si no hay dato (JSON no admite NaN)."""
    return None if pd.isna(valor) else round(float(valor), decimales)


def _estado(alerta) -> str:
    """El semaforo como texto; un mes sin historia suficiente es 'sin dato', no verde."""
    return "sin dato" if pd.isna(alerta) else str(alerta)


def precios_con_nacional(precios: pd.DataFrame) -> pd.DataFrame:
    """Los precios por mercado mas una serie 'Nacional' (la mediana de los mercados).

    Solo meses cerrados: el mes en curso tiene pocos dias y su promedio cambia.
    """
    cerrados = precios[precios["mes_cerrado"]]
    nacional = vigilancia.retornos_nacionales(precios)[["producto", "periodo", "precio_cop_kg"]]
    return pd.concat([cerrados[["mercado", "producto", "periodo", "precio_cop_kg"]],
                      nacional.assign(mercado=NACIONAL)], ignore_index=True)


def armar_tablero(precios: pd.DataFrame, pronosticos: pd.DataFrame) -> dict:
    """Una fila por producto y mercado con todo lo que pinta el tablero.

    precios:     col_precio_mayorista_mensual
    pronosticos: resultado_pronostico_precio (solo existe para el precio nacional)
    """
    todos = precios_con_nacional(precios)
    # Los dos semaforos: frente al mes pasado y frente al mismo mes del anio pasado.
    calculado = volatilidad.comparacion_anual(volatilidad.alertas(todos))
    ultimo = int(calculado["periodo"].max())
    ventana = [_sumar_meses(ultimo, -k) for k in range(MESES_DE_HISTORIA - 1, -1, -1)]

    futuros = pronosticos[pronosticos["tipo"] == "pronostico"].sort_values("horizonte")
    filas = []
    for (mercado, producto), serie in calculado.groupby(["mercado", "producto"]):
        hoy = serie[serie["periodo"] == ultimo]
        if hoy.empty:          # ese mercado no tuvo precio el ultimo mes: no hay nada que comparar
            continue
        hoy = hoy.iloc[0]
        por_periodo = serie.set_index("periodo")["precio_cop_kg"]
        fila = {
            "producto": nombre_producto(producto),
            "mercado": NACIONAL if mercado == NACIONAL else nombre_mercado(mercado),
            "precio": _numero(hoy["precio_cop_kg"], 0),
            "cambio_mes_pct": _numero((np.exp(hoy["retorno_log"]) - 1) * 100),
            "estado_mes": _estado(hoy["alerta"]),
            "z_mes": _numero(hoy["z_score"], 2),
            "cambio_anio_pct": _numero(hoy["cambio_anual_pct"]),
            "estado_anio": _estado(hoy["alerta_anual"]),
            "z_anio": _numero(hoy["z_anual"], 2),
            # Un mes sin precio va como null: en la grafica se ve el hueco, no una linea inventada.
            "serie": [_numero(por_periodo.get(p), 0) for p in ventana],
            "pronostico": None,
        }
        if mercado == NACIONAL:
            futuro = futuros[futuros["producto"] == producto]
            if not futuro.empty:
                a_un_mes = futuro.iloc[0]
                fila["pronostico"] = {
                    "meses": [{"periodo": int(f.periodo), "valor": _numero(f.valor, 0),
                               "minimo": _numero(f.lim_inf, 0), "maximo": _numero(f.lim_sup, 0),
                               "metodo": f.modelo, "confiable": bool(f.gana_al_ingenuo)}
                              for f in futuro.itertuples()],
                    # La confianza es la del pronostico a un mes: se gana solo si el modelo
                    # se equivoca menos que suponer que el precio sigue igual.
                    "confiable": bool(a_un_mes["gana_al_ingenuo"]),
                    "error_modelo_pct": _numero(a_un_mes["mae_modelo"]),
                    "error_ingenuo_pct": _numero(a_un_mes["mae_ingenuo"]),
                }
        filas.append(fila)

    mercados = sorted({f["mercado"] for f in filas} - {NACIONAL})
    return {
        "ultimo_mes": ultimo,
        "ultimo_mes_texto": nombre_mes(ultimo),
        "generado": date.today().isoformat(),
        "periodos": ventana,
        "mercados": [NACIONAL] + mercados,
        "umbrales": {"amarilla": volatilidad.UMBRAL_AMARILLA, "roja": volatilidad.UMBRAL_ROJA},
        "filas": filas,
    }


def main() -> int:
    con = duckdb.connect(str(BASE_DUCKDB), read_only=True)
    precios = con.execute("SELECT * FROM col_precio_mayorista_mensual").df()
    pronosticos = con.execute("SELECT * FROM resultado_pronostico_precio").df()
    con.close()

    tablero = armar_tablero(precios, pronosticos)
    SALIDA.mkdir(parents=True, exist_ok=True)
    destino = SALIDA / "tablero.json"
    destino.write_text(json.dumps(tablero, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(f"{destino.relative_to(RAIZ)}: {len(tablero['filas'])} filas, "
          f"ultimo mes {tablero['ultimo_mes_texto']}, {destino.stat().st_size / 1024:.0f} KB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
