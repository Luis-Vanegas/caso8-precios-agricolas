# Fuentes propias de la app

Archivos que la app necesita y que no vienen de las seis fuentes del pipeline. Las fuentes de
datos (SIPSA, FAOSTAT, NASA POWER, ONI, Pink Sheet, IDEAM) están en
`docs/fuentes_y_referencias.md` y `docs/verificacion_api.md`.

## `config/geo/colombia_departamentos.geojson`

Geometría de los 33 departamentos de Colombia, para colorear el mapa por departamento.

| | |
|---|---|
| Origen | Gist de John Guerra, archivo `Colombia.geo.json` |
| URL | https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/be6a6e239cd5b5b803c6e7c2ec405b793a9064dd/Colombia.geo.json |
| Cadena de origen | El gist declara que es una conversión con `ogr2ogr` de los shapefiles de Colombia de **Maurix Suárez**. John Guerra declara no haber construido la geometría |
| Licencia | **No declara ninguna.** Ver "El problema de la licencia" abajo |
| Descargado y verificado | 2026-10-09 |
| Tamaño | 1,5 MB · 33 features · `Polygon` y `MultiPolygon` |
| Propiedades | `DPTO`, `NOMBRE_DPT`, `AREA`, `PERIMETER`, `HECTARES` |

### Lo que se verificó contra el archivo real

- **33 features**, uno por departamento.
- `DPTO` es el código DANE de dos dígitos **como texto, con el cero a la izquierda** (`05`, `08`).
  Si se lee como número, Antioquia pasa de `05` a `5` y el cruce con la base falla.
- Los 33 códigos de `DPTO` coinciden **exactamente** con `config/departamentos.csv`: ninguno
  sobra y ninguno falta.
- En esta versión del archivo los nombres **no** tienen la codificación dañada: `NARIÑO` se lee
  bien. El aviso de `TASKS.md` sobre `NARIÃ‘O` corresponde a otra copia del archivo.

### Por qué el mapa se une por código y nunca por nombre

Aunque los 33 códigos calzan, **3 de los 33 nombres no calzan** con los de la base:

| `DPTO` | `NOMBRE_DPT` del GeoJSON | `departamento` en `config/departamentos.csv` |
|---|---|---|
| `11` | `SANTAFE DE BOGOTA D.C` | `Bogota` |
| `52` | `NARIÑO` | `Narino` |
| `88` | `ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA` | `San Andres` |

Unir por nombre perdería esos tres departamentos en silencio: el mapa los dibujaría grises como
si no tuvieran datos. **Siempre se une `DPTO` contra `dpto_codigo`** (de `dim_mercado` o de
`config/departamentos.csv`). La prueba `test_el_geojson_cruza_con_los_departamentos_de_la_base`
en `tests/test_app.py` falla si esa correspondencia se rompe.

### El problema de la licencia

El gist no declara licencia, y la geometría es de un tercero (Maurix Suárez). Para un trabajo
académico con fuentes citadas esto es una debilidad que **hay que decir en la sustentación** si
alguien pregunta por el mapa.

La alternativa oficial y citable es el **Marco Geoestadístico Nacional (MGN) del DANE**, que
publica la geometría departamental con términos de uso explícitos:
<https://geoportal.dane.gov.co/servicios/descarga-y-metadatos/descarga-mgn-marco-geoestadistico-nacional/>

Se usa el gist porque el MGN se descarga como shapefile (varios archivos, decenas de MB) y
convertirlo pide una librería geoespacial que el proyecto no tiene. Si el curso exige fuente
oficial para el entregable, el cambio es: descargar el MGN, convertirlo a GeoJSON y reemplazar
este archivo conservando la propiedad `DPTO`. **Nada más del código cambia**, porque el mapa
nunca depende de los nombres.
