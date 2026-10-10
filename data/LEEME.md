# data/ — los datos del proyecto

| Carpeta | Qué hay | ¿Va en git? |
|---|---|---|
| `raw/<fuente>/<fecha>/` | Descargas tal como llegan de cada fuente | No (la crea `scripts/actualizar.py`) |
| `interim/` | Tablas limpias en parquet | No (la crea `scripts/preparar.py`) |
| `processed/caso8.duckdb` | La base final que usa la app | Sí |
| `openrefine/` | Catálogo crudo y recetas JSON de OpenRefine | Sí |

Qué NO tocar:
- `raw/` es **inmutable**: nunca se edita a mano un archivo descargado.
- `processed/caso8.duckdb` solo lo sube a git Claude 1 en su PR de datos.
- Cerrar la app antes de regenerar la base (Windows bloquea el archivo).

Siguiente paso: cómo consultar la base, en el [README](../README.md#dónde-está-cada-cosa).
