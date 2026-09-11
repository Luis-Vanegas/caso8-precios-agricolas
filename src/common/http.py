"""Cliente HTTP compartido: reintentos con backoff exponencial y limite de tasa.

Los reintentos los hace urllib3 a traves de `HTTPAdapter`, no un bucle escrito a
mano: ya resuelve el backoff, el jitter y el respeto de `Retry-After`.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

log = logging.getLogger(__name__)

AGENTE = "caso8-volatilidad/0.1 (proyecto academico ITM)"
TIMEOUT = 120

# Codigos que vale la pena reintentar: rate limit y fallas transitorias del servidor.
_REINTENTOS = Retry(
    total=5,
    backoff_factor=1.5,  # 0s, 1.5s, 3s, 6s, 12s
    status_forcelist=(429, 500, 502, 503, 504, 521),
    allowed_methods=("GET", "POST"),
    respect_retry_after_header=True,
)


def sesion() -> requests.Session:
    """Sesion con reintentos configurados para http y https."""
    s = requests.Session()
    s.headers["User-Agent"] = AGENTE
    adaptador = HTTPAdapter(max_retries=_REINTENTOS)
    s.mount("https://", adaptador)
    s.mount("http://", adaptador)
    return s


class LimitadorTasa:
    """Espaciador simple entre peticiones, para fuentes con limite declarado.

    FAOSTAT declara 2 peticiones por segundo. `LimitadorTasa(2)` deja al menos
    medio segundo entre llamadas.
    """

    def __init__(self, por_segundo: float) -> None:
        self._intervalo = 1.0 / por_segundo
        self._ultima = 0.0

    def esperar(self) -> None:
        faltante = self._intervalo - (time.monotonic() - self._ultima)
        if faltante > 0:
            time.sleep(faltante)
        self._ultima = time.monotonic()


def descargar_a_archivo(
    url: str,
    destino: Path,
    ses: requests.Session | None = None,
    forzar: bool = False,
) -> Path:
    """Descarga `url` a `destino` por bloques, sin cargar el cuerpo en memoria.

    Si `destino` ya existe y `forzar` es falso, no vuelve a bajar nada: los datos
    crudos son inmutables y viven en la carpeta del dia, asi que un archivo que ya
    esta es un archivo que ya se descargo.
    """
    if destino.exists() and not forzar:
        log.info("ya existe, no se vuelve a descargar: %s", destino.name)
        return destino

    ses = ses or sesion()
    destino.parent.mkdir(parents=True, exist_ok=True)
    # Se escribe en un temporal y se renombra al final, para que una descarga
    # cortada a la mitad no quede como si estuviera completa.
    temporal = destino.with_suffix(destino.suffix + ".parcial")
    with ses.get(url, timeout=TIMEOUT, stream=True) as r:
        r.raise_for_status()
        with open(temporal, "wb") as salida:
            for bloque in r.iter_content(1 << 20):
                salida.write(bloque)
    temporal.replace(destino)
    log.info("descargado %s (%s bytes)", destino.name, destino.stat().st_size)
    return destino
