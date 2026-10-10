# scripts/ — los comandos que se ejecutan

Se corren desde la raíz del proyecto con `.venv\Scripts\python.exe scripts\<nombre>.py`.

| Script | Qué hace |
|---|---|
| `diario.py` | Todo junto: actualizar + preparar + integrar |
| `actualizar.py` | Descarga lo nuevo de cada fuente (`--solo <fuente>`, `--dry-run`) |
| `carga_inicial.py` | Descarga todo desde cero (igual a `actualizar.py --forzar`) |
| `preparar.py` | Limpia y perfila; escribe `data/interim/` |
| `integrar.py` | Arma el modelo estrella en la base y corre los 29 chequeos |
| `exploracion.py` | Figuras de exploración en `docs/figuras/` |
| `generar_ejemplos.py` | Muestras reales para la app (`app/ejemplos/`) |
| `probe_*.py` | Pruebas manuales contra las fuentes reales (usan internet) |

Siguiente paso: [docs/actualizacion_diaria.md](../docs/actualizacion_diaria.md).
