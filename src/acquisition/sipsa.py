"""SIPSA (DANE): precios mayoristas via servicio SOAP.

Dos correcciones sobre la guia del DANE de 2020, verificadas en Fase 0 y
documentadas en `docs/verificacion_api.md`:

1. El endpoint HTTP que declara el WSDL no procesa SOAP: responde la pagina
   informativa de JAX-WS. Hay que invocar por HTTPS.
2. El binding es SOAP 1.2, o sea `application/soap+xml` y sin cabecera
   `SOAPAction`.

La respuesta de `promediosSipsaCiudad` pesa mas de 100 MB, asi que se escribe a
disco por bloques y se parsea con `iterparse`. Nunca se carga entera en memoria.

Cuidado con los metodos `*Madr`: segun la guia devuelven solo registros no
consultados antes (bandera `enviado`). Por eso esta funcion **siempre** persiste
la respuesta cruda antes de intentar parsearla: si el parseo falla, el dato ya
esta en disco y no se pierde.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path

import defusedxml.ElementTree as ET

from src.common.http import TIMEOUT, sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "sipsa"

# HTTPS, no el HTTP que declara el WSDL.
ENDPOINT = "https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService"
WSDL = "http://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL"
ESPACIO = "http://servicios.sipsa.co.gov.dane/"

# Metodos confirmados leyendo el WSDL. Los cinco sin argumentos.
METODOS_SIN_ARGUMENTO = (
    "promediosSipsaCiudad",
    "promediosSipsaParcial",
    "promediosSipsaSemanaMadr",
    "promediosSipsaMesMadr",
    "promedioAbasSipsaMesMadr",
)

# Solo este esta verificado como idempotente: dos llamadas devolvieron los mismos
# 383545 registros. Los demas pueden filtrar por la bandera `enviado`, asi que no
# entran en la actualizacion automatica hasta validarlos uno por uno.
METODO_PREDETERMINADO = "promediosSipsaCiudad"


def _sobre(metodo: str) -> bytes:
    """Arma el sobre SOAP 1.2 para un metodo sin argumentos."""
    return (
        '<soap:Envelope xmlns:soap="http://www.w3.org/2003/05/soap-envelope" '
        f'xmlns:ser="{ESPACIO}">'
        f"<soap:Body><ser:{metodo}/></soap:Body></soap:Envelope>"
    ).encode("utf-8")


def invocar(metodo: str, destino: Path, ses=None) -> Path:
    """Llama un metodo SOAP y vuelca la respuesta cruda a `destino`.

    Escribe por bloques: la respuesta puede pesar cientos de megas.
    """
    if metodo not in METODOS_SIN_ARGUMENTO:
        raise ValueError(f"metodo no soportado sin argumentos: {metodo}")
    ses = ses or sesion()
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".parcial")
    with ses.post(
        ENDPOINT,
        data=_sobre(metodo),
        headers={"Content-Type": "application/soap+xml; charset=utf-8"},
        timeout=TIMEOUT * 5,  # la respuesta completa tarda varios minutos
        stream=True,
    ) as r:
        r.raise_for_status()
        if "soap+xml" not in r.headers.get("Content-Type", ""):
            raise RuntimeError(
                f"respuesta no es SOAP ({r.headers.get('Content-Type')}); "
                "revisar que el endpoint siga siendo HTTPS"
            )
        with open(parcial, "wb") as salida:
            for bloque in r.iter_content(1 << 20):
                salida.write(bloque)
    parcial.replace(destino)
    return destino


def leer_registros(ruta: Path) -> list[dict]:
    """Parsea un volcado SOAP a una lista de diccionarios, sin cargarlo entero.

    Campos reales de `promediosSipsaCiudad`: ciudad, codProducto, enviado,
    fechaCaptura, fechaCreacion, precioPromedio, producto, regId.
    """
    registros: list[dict] = []
    for _, elemento in ET.iterparse(str(ruta), events=("end",)):
        etiqueta = elemento.tag.rsplit("}", 1)[-1]
        if etiqueta != "return":
            continue
        registros.append(
            {hijo.tag.rsplit("}", 1)[-1]: hijo.text for hijo in elemento}
        )
        # Liberar el nodo ya procesado: sin esto el arbol crece hasta ocupar
        # varias veces el tamano del archivo.
        elemento.clear()
    return registros


def _ultima_captura(registros: list[dict]) -> str | None:
    """Mayor `fechaCaptura` de la tanda, en formato AAAA-MM-DD."""
    fechas = [r.get("fechaCaptura") for r in registros if r.get("fechaCaptura")]
    return max(fechas)[:10] if fechas else None


def estado() -> EstadoFuente:
    """Comprueba que el WSDL responda. No invoca metodos: cada llamada pesa.

    La frescura real se lee de `meta_actualizacion`, como indica el CLAUDE.md.
    """
    try:
        r = sesion().get(WSDL, timeout=60)
        r.raise_for_status()
        vivo = b"SrvSipsaUpraBeanService" in r.content
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    return EstadoFuente(
        fuente=FUENTE,
        disponible=vivo,
        detalle="WSDL responde" if vivo else "WSDL con contenido inesperado",
    )


def descargar(metodo: str = METODO_PREDETERMINADO, forzar: bool = False) -> ResultadoDescarga:
    """Invoca el metodo, guarda el crudo y reporta cuantos registros trajo."""
    destino = carpeta_cruda(FUENTE) / f"{metodo}.xml"
    if destino.exists() and not forzar:
        registros = leer_registros(destino)
        return ResultadoDescarga(
            FUENTE,
            "cache",
            archivos=[str(destino)],
            filas=len(registros),
            ultimo_periodo=_ultima_captura(registros),
            mensaje=f"ya descargado hoy ({metodo})",
        )
    try:
        invocar(metodo, destino)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")

    try:
        registros = leer_registros(destino)
    except Exception as exc:
        # El crudo ya esta en disco: se reporta el fallo pero el dato no se perdio.
        return ResultadoDescarga(
            FUENTE,
            "error",
            archivos=[str(destino)],
            mensaje=f"descargado pero ilegible: {type(exc).__name__}: {exc}",
        )

    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok",
        archivos=[str(destino)],
        filas=len(registros),
        ultimo_periodo=_ultima_captura(registros),
        fecha_actualizacion_fuente=datetime.now(),
        mensaje=metodo,
    )
