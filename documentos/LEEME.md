# documentos/ — material de consulta para el equipo

Aquí va el material para leer, no el código ni los datos.

| Carpeta | Qué va |
|---|---|
| [articulos/](articulos/LEEME.md) | PDF de referencia (artículos científicos) |
| [curso/](curso/LEEME.md) | Guía AE2 y rúbricas del curso |
| [presentaciones/](presentaciones/LEEME.md) | Diapositivas de la sustentación |
| [informe/](informe/LEEME.md) | Borradores del informe, redactados por el equipo |

**PDF grandes**: git no puede filtrar archivos por tamaño. No subir PDF de más de 10 MB; para
esos, guardar solo el enlace en el `LEEME.md` de la subcarpeta. Si un PDF pesado debe quedarse
en el equipo sin subirse, nombrarlo `<nombre>_grande.pdf` y git lo ignora.

La documentación técnica (guías, contrato de datos, reporte) está en [docs/](../docs/LEEME.md).

## Glosario

| Término | Significado en este proyecto |
|---|---|
| raw | Datos crudos tal como se descargan, en `data/raw/<fuente>/<fecha>/`; nunca se editan |
| interim | Datos intermedios ya limpios (parquet y CSV) en `data/interim/`, escritos por `scripts/preparar.py` |
| processed | Datos finales: la base `data/processed/caso8.duckdb` que lee la app |
| fact | Tabla de hechos (`fact_*`): las mediciones, como precios, clima o producción, una fila por observación |
| dim | Tabla de dimensión (`dim_*`): las descripciones con las que se filtra, como tiempo, mercado o producto |
| puente | Tabla que une dos vocabularios en una relación de muchos a muchos: `puente_producto` (producto SIPSA ↔ ítem FAO) y `puente_zona_sipsa` (producto SIPSA ↔ zona productora) |
| backtest | Simular que se pronosticaba en el pasado, mes a mes, para medir el error real del pronóstico (`src/indicators/pronostico.py`) |
| q-valor | p-valor corregido porque se hacen muchas pruebas a la vez (Benjamini-Hochberg); se considera señal si q < 0,1 |
| art_id | Código del artículo en SIPSA (el `artiId` del DANE); identifica el producto sin depender de su nombre |
| fuen_id | Código del mercado mayorista en SIPSA (el `fuenId`); un mismo mercado puede tener dos nombres, pero un solo código |
| ENSO / ONI | ENSO es el fenómeno El Niño / La Niña; el ONI (NOAA) es su índice: la anomalía de temperatura del mar en la región Niño 3.4, en media móvil de tres meses |
