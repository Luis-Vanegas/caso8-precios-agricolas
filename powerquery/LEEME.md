# powerquery/ — consultas de Power Query (entregable en Excel)

Power Query es uno de los tres entregables obligatorios, junto con Python y OpenRefine.
Cada archivo `.pq` es una consulta que se pega en el editor avanzado de Excel, en orden:

- `00_Parametros.pq`: carpeta raíz del proyecto (lo único que se cambia al mover de equipo).
- `01_SipsaMensual.pq` a `07_SipsaAbastecimiento.pq`: SIPSA, FAOSTAT, base integrada, ENSO, clima, zonas y abastecimiento.

Leen los CSV de `data/interim/`, así que antes hay que correr `scripts/preparar.py`.

Siguiente paso: los pasos en Excel están en [docs/guia_powerquery.md](../docs/guia_powerquery.md).
