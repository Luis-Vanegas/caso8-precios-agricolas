"""Fase 0: verifica cual URL base de la API de FAOSTAT responde y si exige token.

No asume nada: prueba las dos URL base candidatas, con y sin token, y guarda
la evidencia cruda en data/raw/_probe/faostat_api/.

Uso:
    python scripts/probe_faostat_api.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "raw" / "_probe" / "faostat_api"

# Las dos URL base que la documentacion reporta como contradictorias.
BASES = {
    "faostatservices": "https://faostatservices.fao.org/api/v1",
    "fenixservices": "https://fenixservices.fao.org/faostat/api/v1",
}

# Rutas candidatas: listado de dominios y una consulta chica a Producer Prices
# de Colombia (area 44 segun FAO). Si la ruta no existe lo vamos a ver en el codigo.
RUTAS = {
    "groups": "/en/groups",
    "domains": "/en/domains",
    "pp_colombia": "/en/data/PP?area=44&year=2022&page_size=5",
}

TIMEOUT = 30


def probar(nombre_base: str, base: str, token: str | None) -> list[dict]:
    """Golpea cada ruta candidata de una URL base y devuelve un resumen por ruta."""
    etiqueta = "con_token" if token else "sin_token"
    cabeceras = {"User-Agent": "caso8-volatilidad/0.1 (probe fase 0)"}
    if token:
        # El cliente comunitario usa cabecera; probamos tambien query param mas abajo.
        cabeceras["Authorization"] = f"Bearer {token}"

    resultados = []
    for nombre_ruta, ruta in RUTAS.items():
        url = base + ruta
        registro: dict = {"base": nombre_base, "ruta": nombre_ruta, "url": url, "auth": etiqueta}
        try:
            r = requests.get(url, headers=cabeceras, timeout=TIMEOUT)
            registro["status"] = r.status_code
            registro["content_type"] = r.headers.get("Content-Type", "")
            registro["bytes"] = len(r.content)
            cuerpo = r.text[:2000]
            registro["muestra"] = cuerpo
            archivo = SALIDA / f"{nombre_base}__{nombre_ruta}__{etiqueta}.txt"
            archivo.write_text(r.text[:200000], encoding="utf-8", errors="replace")
            registro["evidencia"] = str(archivo.relative_to(RAIZ))
        except requests.RequestException as exc:
            registro["status"] = None
            registro["error"] = f"{type(exc).__name__}: {exc}"
        resultados.append(registro)
        print(f"  {nombre_base:18} {nombre_ruta:12} {etiqueta:10} -> {registro.get('status') or registro.get('error')}")
    return resultados


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    token = os.environ.get("FAOSTAT_API_KEY") or None
    print(f"Token FAOSTAT en entorno: {'si' if token else 'NO'}")

    todos: list[dict] = []
    for nombre, base in BASES.items():
        print(f"\n[{nombre}] {base}")
        todos += probar(nombre, base, None)
        if token:
            todos += probar(nombre, base, token)

    resumen = SALIDA / "resumen.json"
    resumen.write_text(json.dumps(todos, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResumen: {resumen.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
