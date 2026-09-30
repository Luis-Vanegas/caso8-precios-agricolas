"""IDEAM: lecturas reales de sensores de estaciones automaticas (datos.gov.co).

Es la fuente de tipo sensor del proyecto. A diferencia de NASA POWER, que es un
producto modelado sobre una grilla, aca cada fila es la lectura de un sensor
fisico en una estacion con codigo, municipio y coordenadas propias.

Verificado el 2026-09-22 contra la ficha de la API Socrata de datos.gov.co:

| Variable      | Dataset     | Frecuencia declarada | Unidad | Filas        |
|---------------|-------------|----------------------|--------|--------------|
| Precipitacion | `s54a-sgyg` | cada 10 minutos      | mm     | ~116 millones|
| Temperatura   | `sbwg-7ju4` | cada hora            | °C     |              |

Columnas reales: codigoestacion, codigosensor, fechaobservacion, valorobservado,
nombreestacion, departamento, municipio, zonahidrografica, latitud, longitud,
descripcionsensor, unidadmedida. `valorobservado` es numerico.

Con ~116 millones de lecturas no se baja el crudo: se agrega en el servidor con
SoQL (suma, promedio, minimo, maximo y conteo por estacion y mes). Se pide un
departamento y UN MES por consulta para que ninguna se acerque al timeout.

# Verificado el 2026-09-23 contra la API real con scripts/probe_ideam.py:
#   - Norte de Santander estaba mal en NOMBRE_IDEAM ("Norte de Santander" con
#     "de" minuscula); el dataset lo publica como "Norte De Santander". Los
#     demas nombres con tilde ya eran correctos (Boyacá, Quindío, etc.)
#   - CADA departamento existe DOS VECES en el dataset con distinta convencion
#     de mayusculas ("Boyaca" vs "BOYACA"). No son duplicados: para una misma
#     estacion, cada variante cubre meses distintos y sin solapar (IDEAM
#     migro de convencion a mitad de 2026). _paginas pide las dos variantes
#     por igualdad exacta y las junta.
#   - Probado y descartado: comparar con upper(departamento) = upper(...)
#     junta las dos variantes en una sola consulta, pero le rompe a Socrata
#     el uso del indice sobre `departamento` y el agregado empieza a dar
#     timeout. La igualdad exacta responde rapido; por eso se pide dos veces
#     (una por variante) en vez de una vez con upper().
#   - El agregado por departamento-anio COMPLETO da timeout para los
#     departamentos con mas estaciones (ej. BOYACÁ, ~1.6 millones de lecturas
#     en 2026), y partido por semestre o por trimestre TAMBIEN da timeout. El
#     cuello de botella es el volumen de lecturas agregadas server-side, no
#     la cantidad de columnas del $group. Por mes si responde (15-30s en los
#     casos mas pesados probados): por eso se pide mes a mes, nunca el anio
#     ni el semestre completo.
#   - Boyaca no tiene lecturas antes de 2026 (hueco real de la red de
#     estaciones, no un error de nombre): se declara, no se rellena.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import date, datetime, timezone

from src.acquisition.nasa_power import zonas
from src.common.http import sesion
from src.common.modelos import EstadoFuente, ResultadoDescarga
from src.common.rutas import carpeta_cruda

log = logging.getLogger(__name__)

FUENTE = "ideam"
BASE = "https://www.datos.gov.co"

# variable -> (dataset, agregado principal que tiene sentido fisico por mes)
# La lluvia se acumula (suma); la temperatura se promedia.
VARIABLES: dict[str, dict] = {
    "precipitacion": {"dataset": "s54a-sgyg", "unidad": "mm"},
    "temperatura": {"dataset": "sbwg-7ju4", "unidad": "°C"},
}

# El servicio web de SIPSA arranca en febrero de 2020: se alinea con el.
ANIO_INICIO = 2020

# Los nombres de config van sin tilde; IDEAM los publica con tilde.
# Es la variable de integracion con las zonas productoras, asi que un nombre mal
# escrito no falla: devuelve cero filas en silencio. Por eso esta explicito.
NOMBRE_IDEAM = {
    "Antioquia": "Antioquia",
    "Boyaca": "Boyacá",
    "Cundinamarca": "Cundinamarca",
    "Huila": "Huila",
    "Meta": "Meta",
    "Norte de Santander": "Norte De Santander",
    "Quindio": "Quindío",
    "Tolima": "Tolima",
}

LIMITE_PAGINA = 50_000


def departamentos() -> list[str]:
    """Departamentos de las zonas productoras, sin repetir y en el orden de config."""
    vistos: list[str] = []
    for zona in zonas():
        if zona["departamento"] not in vistos:
            vistos.append(zona["departamento"])
    return vistos


def _encabezados() -> dict[str, str]:
    """Token de aplicacion opcional. Sin el, Socrata atiende con limite de tasa."""
    token = os.getenv("SOCRATA_APP_TOKEN")
    return {"X-App-Token": token} if token else {}


def _limites_mes(anio: int, mes: int) -> tuple[str, str]:
    """Rango [desde, hasta) de un mes calendario."""
    if mes == 12:
        return f"{anio}-12-01T00:00:00", f"{anio + 1}-01-01T00:00:00"
    return f"{anio}-{mes:02d}-01T00:00:00", f"{anio}-{mes + 1:02d}-01T00:00:00"


def consulta_mensual(
    departamento_ideam: str, anio: int, mes: int, offset: int = 0
) -> dict[str, str]:
    """Parametros SoQL para agregar las lecturas de UN MES por estacion y sensor.

    Se agrupa tambien por codigo de sensor: una estacion puede tener dos
    sensores de la misma variable (convencional y GPRS) y mezclarlos sumaria la
    lluvia dos veces.

    `departamento_ideam` tiene que ser el nombre EXACTO (mayusculas incluidas)
    que usa el dataset: la igualdad simple usa el indice de Socrata. Envolverlo
    en upper() para ignorar mayusculas rompe ese indice (verificado con
    scripts/probe_ideam.py); por eso _paginas pide las dos variantes de
    mayusculas por separado en vez de una sola comparacion con upper().

    Se pide UN MES a la vez, nunca el anio ni el semestre completo: para los
    departamentos con mas estaciones (ej. BOYACÁ, ~1.6 millones de lecturas en
    2026) el agregado por semestre y hasta por trimestre da timeout aunque la
    igualdad sea exacta. Por mes responde en 15-30s (probado contra la API
    real); el cuello de botella es el volumen de lecturas agregadas, no la
    cantidad de columnas del $group ni el uso del indice.
    """
    desde, hasta = _limites_mes(anio, mes)
    grupo = (
        "codigoestacion, codigosensor, nombreestacion, departamento, municipio, "
        "latitud, longitud, mes"
    )
    return {
        "$select": (
            f"{grupo.replace(', mes', '')}, "
            "date_trunc_ym(fechaobservacion) AS mes, "
            "sum(valorobservado) AS suma, avg(valorobservado) AS promedio, "
            "min(valorobservado) AS minimo, max(valorobservado) AS maximo, "
            "count(valorobservado) AS n_lecturas"
        ),
        "$where": (
            f"departamento = '{departamento_ideam}' "
            f"AND fechaobservacion >= '{desde}' "
            f"AND fechaobservacion < '{hasta}'"
        ),
        "$group": grupo,
        "$order": "codigoestacion, codigosensor, mes",
        "$limit": str(LIMITE_PAGINA),
        "$offset": str(offset),
    }


def consulta_muestra(codigo_estacion: str, desde: str, limite: int = 2000) -> dict[str, str]:
    """Lecturas crudas de una estacion: la evidencia de como sale el dato del sensor."""
    return {
        "$where": f"codigoestacion = '{codigo_estacion}' AND fechaobservacion >= '{desde}'",
        "$order": "fechaobservacion",
        "$limit": str(limite),
    }


def fecha_actualizacion(dataset: str, ses=None) -> datetime:
    """`rowsUpdatedAt` de la ficha del dataset: epoch en segundos."""
    ses = ses or sesion()
    r = ses.get(f"{BASE}/api/views/{dataset}.json", headers=_encabezados(), timeout=60)
    r.raise_for_status()
    return datetime.fromtimestamp(int(r.json()["rowsUpdatedAt"]), tz=timezone.utc)


def estado() -> EstadoFuente:
    """Fecha de actualizacion de la precipitacion, que es la variable principal."""
    try:
        fecha = fecha_actualizacion(VARIABLES["precipitacion"]["dataset"])
    except Exception as exc:
        return EstadoFuente(FUENTE, disponible=False, detalle=f"{type(exc).__name__}: {exc}")
    return EstadoFuente(
        fuente=FUENTE,
        disponible=True,
        ultimo_periodo=fecha.date().isoformat(),
        fecha_actualizacion_fuente=fecha.replace(tzinfo=None),
        detalle="rowsUpdatedAt del dataset de precipitacion",
    )


def _paginas(ses, dataset: str, departamento_ideam: str, anio: int) -> list[dict]:
    """Recorre mes a mes las dos variantes de mayusculas del departamento.

    IDEAM publica cada departamento con dos convenciones de mayusculas
    ("Boyaca" y "BOYACA") que se reparten el tiempo: verificado con
    scripts/probe_ideam.py que para una misma estacion no hay meses en comun
    entre una variante y la otra, asi que juntarlas no duplica lecturas.
    """
    filas: list[dict] = []
    for variante in {departamento_ideam, departamento_ideam.upper()}:
        for mes in range(1, 13):
            offset = 0
            while True:
                r = ses.get(
                    f"{BASE}/resource/{dataset}.json",
                    params=consulta_mensual(variante, anio, mes, offset),
                    headers=_encabezados(),
                    timeout=90,
                )
                r.raise_for_status()
                pagina = r.json()
                filas.extend(pagina)
                if len(pagina) < LIMITE_PAGINA:
                    break
                offset += LIMITE_PAGINA
    return filas


def descargar(desde: datetime | None = None, forzar: bool = False) -> ResultadoDescarga:
    """Un JSON por variable, departamento y anio, mas una muestra cruda de 10 minutos.

    Los anios cerrados se reutilizan si ya estan en disco; el anio en curso se
    vuelve a pedir siempre, porque sigue recibiendo lecturas.
    """
    destino = carpeta_cruda(FUENTE)
    ses = sesion()
    hoy = date.today()
    archivos: list[str] = []
    errores: list[str] = []
    filas = 0

    for variable, meta in VARIABLES.items():
        for depto in departamentos():
            nombre_ideam = NOMBRE_IDEAM.get(depto, depto)
            for anio in range(ANIO_INICIO, hoy.year + 1):
                archivo = destino / f"{variable}_{depto}_{anio}.json".replace(" ", "_")
                if archivo.exists() and not forzar and anio < hoy.year:
                    archivos.append(str(archivo))
                    continue
                try:
                    datos = _paginas(ses, meta["dataset"], nombre_ideam, anio)
                except Exception as exc:
                    errores.append(f"{archivo.name}: {type(exc).__name__}")
                    continue
                archivo.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
                archivos.append(str(archivo))
                filas += len(datos)

    muestra = _guardar_muestra(ses, destino)
    if muestra:
        archivos.append(muestra)

    if errores and not archivos:
        return ResultadoDescarga(FUENTE, "error", mensaje="; ".join(errores))
    return ResultadoDescarga(
        fuente=FUENTE,
        estado="ok" if filas else "cache",
        archivos=archivos,
        filas=filas or None,
        ultimo_periodo=hoy.isoformat(),
        mensaje="; ".join(errores[:5]),
    )


def _guardar_muestra(ses, destino) -> str | None:
    """Ultimos 7 dias de la estacion con mas lecturas en el primer departamento.

    Sirve de evidencia para la seccion de adquisicion (DAQ): muestra el dato tal
    como lo entrega el sensor, antes de cualquier agregacion.
    """
    depto = departamentos()[0]
    archivo_anio = destino / f"precipitacion_{depto}_{date.today().year}.json".replace(" ", "_")
    if not archivo_anio.exists():
        return None
    agregados = json.loads(archivo_anio.read_text(encoding="utf-8"))
    if not agregados:
        return None
    estacion = max(agregados, key=lambda f: int(f.get("n_lecturas", 0)))["codigoestacion"]
    desde = date.fromordinal(date.today().toordinal() - 7).isoformat() + "T00:00:00"
    try:
        r = ses.get(
            f"{BASE}/resource/{VARIABLES['precipitacion']['dataset']}.json",
            params=consulta_muestra(estacion, desde),
            headers=_encabezados(),
            timeout=120,
        )
        r.raise_for_status()
    except Exception as exc:
        log.warning("no se pudo bajar la muestra cruda: %s", exc)
        return None
    salida = destino / "muestra_precipitacion_cruda.json"
    salida.write_text(json.dumps(r.json(), ensure_ascii=False, indent=1), encoding="utf-8")
    return str(salida)
