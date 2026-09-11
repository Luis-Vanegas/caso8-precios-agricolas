"""Fase 0: verifica las fuentes que no son la API REST de FAOSTAT.

Comprueba disponibilidad y formato real de:
  - catalogo XML de descargas masivas FAOSTAT
  - WSDL del servicio SOAP de SIPSA (DANE)
  - OpenAPI mensual de NASA POWER
  - archivo ONI de NOAA CPC
  - pagina Pink Sheet del Banco Mundial

Guarda todo crudo en data/raw/_probe/<fuente>/ y un resumen JSON.

Uso:
    python scripts/probe_fuentes.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import requests

RAIZ = Path(__file__).resolve().parents[1]
SALIDA = RAIZ / "data" / "raw" / "_probe"

CABECERAS = {"User-Agent": "caso8-volatilidad/0.1 (probe fase 0)"}
TIMEOUT = 60

FUENTES = {
    "faostat_bulk": "https://bulks-faostat.fao.org/production/datasets_E.xml",
    "sipsa_wsdl": "http://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL",
    "nasa_power_openapi": "https://power.larc.nasa.gov/api/temporal/monthly/openapi.json",
    "oni": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
    "pink_sheet": "https://www.worldbank.org/en/research/commodity-markets",
}

EXTENSION = {
    "faostat_bulk": "xml",
    "sipsa_wsdl": "xml",
    "nasa_power_openapi": "json",
    "oni": "txt",
    "pink_sheet": "html",
}


def main() -> int:
    SALIDA.mkdir(parents=True, exist_ok=True)
    resultados = []

    for nombre, url in FUENTES.items():
        registro: dict = {"fuente": nombre, "url": url}
        try:
            r = requests.get(url, headers=CABECERAS, timeout=TIMEOUT)
            registro["status"] = r.status_code
            registro["content_type"] = r.headers.get("Content-Type", "")
            registro["bytes"] = len(r.content)
            registro["last_modified"] = r.headers.get("Last-Modified", "")
            destino = SALIDA / nombre
            destino.mkdir(parents=True, exist_ok=True)
            archivo = destino / f"respuesta.{EXTENSION[nombre]}"
            archivo.write_bytes(r.content)
            registro["evidencia"] = str(archivo.relative_to(RAIZ))
            registro["muestra"] = r.text[:1500]
        except requests.RequestException as exc:
            registro["status"] = None
            registro["error"] = f"{type(exc).__name__}: {exc}"
        print(f"{nombre:20} -> {registro.get('status') or registro.get('error')}  "
              f"{registro.get('bytes', '')}")
        resultados.append(registro)

    resumen = SALIDA / "resumen_fuentes.json"
    resumen.write_text(json.dumps(resultados, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResumen: {resumen.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
