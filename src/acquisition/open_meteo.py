"""Open-Meteo: clima diario observado, pronostico a 16 dias y estacional a 6 meses.

Es el "clima en tiempo real" del proyecto y lo que permite mirar hacia adelante.
No pide token. Un punto por departamento productor (las mismas coordenadas de
`config/zonas_productoras.json` que usa NASA POWER).

Tres consultas por departamento, verificadas el 2026-10-09 (Tunja):
- observado  (archive-api):  diario desde 2020-01-01 hasta ayer, sin vacios.
- pronostico (api):          16 dias hacia adelante.
- estacional (seasonal-api): 183 dias, con la serie base y 50 miembros de
  ensamble (escenarios). Los ultimos dias pueden llegar vacios (None).

Variables: lluvia diaria (mm) y temperatura maxima y minima (°C), en hora de
Colombia. Se guarda la respuesta cruda tal cual; la limpieza la convierte en tablas.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from pathlib import Path

from src.acquisition.nasa_power import zonas
from src.common.http import sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

FUENTE = "open_meteo"

ENDPOINTS = {
    "observado": "https://archive-api.open-meteo.com/v1/archive",
    "pronostico": "https://api.open-meteo.com/v1/forecast",
    "estacional": "https://seasonal-api.open-meteo.com/v1/seasonal",
}
VARIABLES = "precipitation_sum,temperature_2m_max,temperature_2m_min"
INICIO_HISTORIA = date(2020, 1, 1)   # SIPSA arranca en 2020: antes no hace falta clima
DIAS_PRONOSTICO = 16
DIAS_ESTACIONAL = 183


def departamentos() -> list[dict]:
    """Un punto por departamento. Boyaca aparece en varias zonas (papa, cebolla):
    se baja una sola vez porque las coordenadas son las mismas."""
    vistos: dict[str, dict] = {}
    for z in zonas():
        vistos.setdefault(z["departamento"], {"departamento": z["departamento"], "lat": z["lat"], "lon": z["lon"]})
    return list(vistos.values())


def consulta(tipo: str, punto: dict, hoy: date | None = None) -> tuple[str, dict]:
    """URL y parametros de una consulta. Separado de la red para poder probarlo."""
    hoy = hoy or date.today()
    params = {"latitude": punto["lat"], "longitude": punto["lon"],
              "daily": VARIABLES, "timezone": "America/Bogota"}
    if tipo == "observado":
        params["start_date"] = INICIO_HISTORIA.isoformat()
        params["end_date"] = (hoy - timedelta(days=1)).isoformat()   # hoy aun no termina
    elif tipo == "pronostico":
        params["forecast_days"] = DIAS_PRONOSTICO
    else:
        params["forecast_days"] = DIAS_ESTACIONAL
    return ENDPOINTS[tipo], params


def dias_con_dato(respuesta: dict) -> int:
    """Cuantos dias traen lluvia reportada (los vacios del estacional no cuentan)."""
    return sum(v is not None for v in respuesta["daily"]["precipitation_sum"])


def estado() -> EstadoFuente:
    """Pide un dia de pronostico para un punto: si responde, el servicio esta vivo.

    La fecha de actualizacion es hoy: el pronostico cambia todos los dias.
    """
    try:
        url, params = consulta("pronostico", departamentos()[0])
        r = sesion().get(url, params={**params, "forecast_days": 1}, timeout=60)
        r.raise_for_status()
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    return EstadoFuente(FUENTE, disponible=True, fecha_actualizacion_fuente=datetime.now(),
                        detalle="pronostico responde")


def descargar(forzar: bool = False) -> ResultadoDescarga:
    """Tres archivos por departamento: <tipo>_<Departamento>.json.

    Se baja todo cada vez: el pronostico cambia a diario y la historia observada
    es liviana (unos 2500 dias por punto).
    """
    destino = carpeta_cruda(FUENTE)
    ses = sesion()
    archivos, errores, ultimo, dias = [], [], None, 0
    for punto in departamentos():
        for tipo in ENDPOINTS:
            archivo = destino / f"{tipo}_{punto['departamento']}.json".replace(" ", "_")
            url, params = consulta(tipo, punto)
            try:
                r = ses.get(url, params=params, timeout=120)
                r.raise_for_status()
                datos = r.json()
                if "daily" not in datos:   # Open-Meteo responde errores como JSON con "reason"
                    raise ValueError(datos.get("reason", "respuesta sin 'daily'"))
            except Exception as exc:
                errores.append(f"{archivo.name}: {type(exc).__name__}: {exc}")
                continue
            archivo.write_bytes(r.content)
            archivos.append(str(archivo))
            if tipo == "observado":
                ultimo = max(ultimo or "", datos["daily"]["time"][-1])
                dias += dias_con_dato(datos)   # filas = dias observados, sumando departamentos

    if errores and not archivos:
        return ResultadoDescarga(FUENTE, "error", mensaje="; ".join(errores))
    return ResultadoDescarga(
        fuente=FUENTE, estado="ok", archivos=archivos, filas=dias,
        ultimo_periodo=ultimo, fecha_actualizacion_fuente=datetime.now(),
        mensaje="; ".join(errores),
    )


def leer_archivo(ruta: Path) -> dict:
    """Abre un JSON descargado. Separado para que la limpieza no dependa de la red."""
    return json.loads(Path(ruta).read_text(encoding="utf-8"))
