"""NASA POWER diario: completa los meses recientes que el endpoint mensual aun no trae.

Por que existe este modulo:
  El endpoint mensual publica con rezago. El 2026-09-11 solo llegaba hasta
  diciembre de 2025; el 2026-09-22 ya traia enero-julio de 2026, pero agosto y
  septiembre venian en -999. El endpoint DIARIO tiene el ano en curso con unos
  dias de rezago, asi que llena esos meses. Donde el mensual ya tiene el dato,
  gana el mensual (ver `unir_clima`).

Verificado el 2026-09-22 contra el servicio real:
  - /temporal/daily/configuration publica la ultima fecha servida (2026-09-22).
  - Los ultimos 3 dias llegan con -999 (el valor de "sin dato" del encabezado).
  - Las unidades son las mismas del mensual: PRECTOTCORR en mm/dia, T2M en °C.
  - El promedio de los dias de un mes da EXACTAMENTE el valor del endpoint
    mensual (Boyaca 2025: enero 2,18 = 2,18; julio 6,15 = 6,15), y la celda
    de grilla y su elevacion son las mismas. Por eso las dos series se pueden
    pegar una detras de la otra sin ajustar nada.
"""

from __future__ import annotations

import json
import logging
from datetime import date, datetime

import pandas as pd

from src.acquisition.nasa_power import COMUNIDAD, PARAMETROS, SIN_DATO, zonas
from src.common.http import sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "nasa_power_diario"
ENDPOINT = "https://power.larc.nasa.gov/api/temporal/daily/point"
CONFIGURACION = "https://power.larc.nasa.gov/api/temporal/daily/configuration"

# Un mes con menos dias que esto no se usa: su promedio seria poco confiable.
MINIMO_DIAS = 10


def ultima_fecha_disponible(ses=None) -> date:
    """Ultimo dia que sirve el endpoint diario, leido del propio servicio."""
    ses = ses or sesion()
    r = ses.get(CONFIGURACION, timeout=60)
    r.raise_for_status()
    return datetime.fromisoformat(r.json()["settings"]["end"]).date()


def a_mensual(respuesta: dict, zona: dict) -> list[dict]:
    """Promedia los dias de cada mes. Devuelve filas iguales a las del endpoint mensual.

    Pasos:
      1. Los -999 (sin dato) se vuelven vacios ANTES de promediar; si no,
         un solo -999 hunde el promedio del mes.
      2. Se promedia por ano y mes y se cuenta cuantos dias tenian dato.
      3. Los meses con menos de MINIMO_DIAS dias se descartan.
    """
    sin_dato = respuesta.get("header", {}).get("fill_value", SIN_DATO)
    filas: list[dict] = []
    for parametro, serie in respuesta["properties"]["parameter"].items():
        s = pd.Series(serie, dtype="float64")
        s.index = pd.to_datetime(s.index, format="%Y%m%d")
        s = s.mask(s == sin_dato)                         # paso 1
        mensual = s.groupby([s.index.year, s.index.month]).agg(["mean", "count"])  # paso 2
        for (anio, mes), fila in mensual.iterrows():
            if fila["count"] < MINIMO_DIAS:               # paso 3
                continue
            filas.append({
                "producto": zona["producto"],
                "departamento": zona["departamento"],
                "lat": zona["lat"],
                "lon": zona["lon"],
                "anio": int(anio),
                "mes": int(mes),
                "parametro": parametro,
                "valor": round(float(fila["mean"]), 2),
                "dias_con_dato": int(fila["count"]),
            })
    return filas


def estado() -> EstadoFuente:
    """La fecha de actualizacion es el ultimo dia servido: cambia casi todos los dias."""
    try:
        fin = ultima_fecha_disponible()
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    return EstadoFuente(
        fuente=FUENTE,
        disponible=True,
        ultimo_periodo=fin.isoformat(),
        fecha_actualizacion_fuente=datetime.combine(fin, datetime.min.time()),
        detalle="ultimo dia servido por el endpoint diario",
    )


def descargar(desde: datetime | None = None, forzar: bool = False) -> ResultadoDescarga:
    """Una consulta por zona con el ano en curso, del 1 de enero al ultimo dia servido.

    Son pocos dias por zona (menos de un ano), asi que se baja completo cada vez:
    los ultimos dias pueden pasar de -999 a un valor real y hay que refrescarlos.
    No se intenta adivinar hasta donde llega el mensual: `unir_clima` decide.
    """
    destino = carpeta_cruda(FUENTE)
    ses = sesion()
    try:
        fin = ultima_fecha_disponible(ses)
    except Exception as exc:
        return ResultadoDescarga(FUENTE, "error", mensaje=f"{type(exc).__name__}: {exc}")
    inicio = date(fin.year, 1, 1)

    archivos, errores, filas = [], [], 0
    for zona in zonas():
        archivo = destino / f"{zona['producto']}_{zona['departamento']}.json".replace(" ", "_")
        try:
            r = ses.get(ENDPOINT, timeout=180, params={
                "start": inicio.strftime("%Y%m%d"), "end": fin.strftime("%Y%m%d"),
                "latitude": zona["lat"], "longitude": zona["lon"],
                "community": COMUNIDAD, "parameters": PARAMETROS, "format": "JSON",
            })
            r.raise_for_status()
        except Exception as exc:
            errores.append(f"{archivo.name}: {type(exc).__name__}")
            continue
        archivo.write_bytes(r.content)
        archivos.append(str(archivo))
        filas += len(a_mensual(r.json(), zona))

    if errores and not archivos:
        return ResultadoDescarga(FUENTE, "error", mensaje="; ".join(errores))
    return ResultadoDescarga(
        fuente=FUENTE, estado="ok", archivos=archivos, filas=filas,
        ultimo_periodo=fin.isoformat(), mensaje="; ".join(errores),
    )


def leer_archivo(ruta) -> dict:
    """Abre un JSON descargado. Separado para que la limpieza no dependa de la red."""
    return json.loads(ruta.read_text(encoding="utf-8"))
