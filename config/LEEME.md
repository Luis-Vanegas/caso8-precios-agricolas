# config/ — tablas de referencia hechas a mano

- `homologacion_productos.csv`: cómo se corresponde cada producto de SIPSA con su ítem de FAO.
- `catalogo_articulos.csv`: artículos de SIPSA por `art_id` (producto, grupo, unidad, si está en la canasta).
- `mercados.csv`, `mercados_sipsa.csv`, `departamentos.csv`: mercados mayoristas, sus coordenadas, su `fuen_id` y su departamento.
- `zonas_productoras.json`: zonas donde se cultiva cada producto (para cruzar con el clima).
- `geo/`: mapa de departamentos de Colombia (GeoJSON) que usa la app.

Qué NO hacer: no cambiar los nombres de las columnas; el código los lee por nombre.
Después de editar un archivo, correr `scripts/preparar.py` y `scripts/integrar.py` para que el cambio llegue a la base.

Siguiente paso: la homologación con OpenRefine se explica en [docs/guia_openrefine.md](../docs/guia_openrefine.md).
