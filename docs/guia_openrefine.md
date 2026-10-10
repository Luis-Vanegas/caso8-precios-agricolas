# Guía de OpenRefine — homologación de productos

> **Atajo sin Python:** abrí la app (local o el link de producción) → **Cómo lo hicimos** → pestaña **Descargar datos**. Ahí bajás cualquier tabla ya limpia en CSV o Excel, o todas las principales en un ZIP con un LEEME. En OpenRefine: `Create Project` → `This Computer` → el CSV descargado (codificación UTF-8).

OpenRefine es uno de los tres entregables obligatorios del reto, junto con Python y Power Query.
Esta guía es el paso que ejecutás vos a mano. Al final exportás el JSON de operaciones a
`data/openrefine/`, que sí se versiona, para que el trabajo sea reproducible.

El archivo de entrada ya está generado: `data/interim/sipsa/sipsa_mensual.csv`.

---

## Por qué este paso existe

FAOSTAT y SIPSA no hablan el mismo idioma. SIPSA publica 33 productos con nombres comerciales
colombianos y FAOSTAT publica ítems de una clasificación internacional. Sin una tabla que los
conecte, las dos fuentes no se pueden cruzar y la base analítica integrada no existe.

La propuesta inicial está en `config/homologacion_productos.csv` y ya viene aplicada en el CSV
de entrada. Lo que hacés en OpenRefine es **revisarla, corregirla y dejar constancia**.

---

## La conclusión incómoda, y hay que decirla en el reporte

La correspondencia **no es uno a uno**. De los 33 productos de SIPSA:

| Tipo de correspondencia | Productos | Qué significa |
|---|---:|---|
| `exacta` | 13 | El ítem de FAO representa el mismo producto |
| `agregada` | 10 | FAO mete varios productos de SIPSA en un solo ítem |
| `generica` | 8 | Cae en un cajón "n.e.c." junto con decenas de productos |
| `sin_equivalente` | 2 | FAO no publica ese producto para Colombia |

Seis ítems de FAO reciben más de un producto de SIPSA:

| Ítem FAO | Productos de SIPSA que caen ahí |
|---|---|
| 116 Potatoes | Papa criolla + Papa negra |
| 463 Other vegetables, fresh n.e.c. | Habichuela + Remolacha |
| 489 Plantains and cooking bananas | Plátano guineo + Plátano hartón verde |
| 497 Lemons and limes | Limón Común + Limón Tahití |
| 571 Mangoes, guavas and mangosteens | Guayaba + Mango tommy |
| 603 Other tropical fruits, n.e.c. | Granadilla + Lulo + Maracuyá + Tomate de árbol |

**Consecuencia directa para el análisis:** el precio productor de FAO para el ítem 571 no es el
precio de la guayaba ni el del mango, es una mezcla. Comparar el precio mayorista de la guayaba
en SIPSA contra ese ítem produce un margen inventado.

Por eso solo los **13 productos con correspondencia exacta** admiten comparar precio mayorista
contra precio productor. Los otros 20 sirven para ubicar el producto en la jerarquía y para
analizar su volatilidad con datos de SIPSA solamente.

Dos casos no tienen ítem en FAO para Colombia:

- **Cebolla junca.** El ítem 402, cebolla en rama, no aparece en los datos de Colombia.
- **Chócolo mazorca.** El ítem 446, maíz dulce, tampoco. El maíz 56 es grano seco, que es otro
  producto y otro mercado.

---

## Pasos en OpenRefine

### 1. Crear el proyecto

`Create Project` → `This Computer` → `data/interim/sipsa/sipsa_mensual.csv`.

En la vista previa, antes de crear:

- **Character encoding:** `UTF-8`. El CSV lleva BOM, así que debería detectarlo solo. Verificá
  que `Limón Tahití` y `Plátano hartón verde` se lean con sus tildes. Si ves caracteres raros,
  el encoding está mal y hay que corregirlo acá, no después.
- **Parse cell text into numbers, dates:** activado.
- `Create Project`.

### 2. Revisar los nombres con facetas

En la columna `producto`: `Facet` → `Text facet`.

Deben aparecer exactamente 33 valores. Ordená por conteo y revisá que no haya variantes del
mismo producto escritas distinto. Si aparecen 34 o más, el DANE agregó un producto y el mapeo
quedó desactualizado.

### 3. Agrupar variantes con Cluster

Con la faceta abierta: `Cluster`.

Probá los métodos en este orden:

1. `key collision` + `fingerprint`
2. `key collision` + `ngram-fingerprint`
3. `nearest neighbor` + `levenshtein`, radio 2

Con 33 productos bien escritos es probable que no encuentre nada, y eso es un resultado válido:
significa que la fuente es consistente. **Dejá constancia igual**, porque el reto pide demostrar
el proceso de limpieza, no solo su resultado.

### 4. Normalizar el texto

Sobre `producto`: `Edit cells` → `Common transforms` → `Trim leading and trailing whitespace`.

Ojo con `Piña *`, que tiene un espacio antes del asterisco. Es la única inconsistencia de
formato de la fuente y conviene dejarla documentada.

No apliques `To uppercase` ni quites tildes: los nombres van al reporte y a la app, y tienen que
leerse bien.

### 5. Revisar la homologación

Las columnas `item_codigo_fao`, `item_fao` y `tipo_correspondencia` ya vienen pegadas.

`Facet` → `Text facet` sobre `tipo_correspondencia`, y revisá producto por producto los que
digan `agregada`, `generica` o `sin_equivalente`. Si no estás de acuerdo con alguna decisión,
cambiala acá y anotá el porqué en la columna `nota`.

Los dos cambios más probables que quieras hacer:

- Mover `Remolacha` de `generica` a `sin_equivalente`, argumentando que "Other vegetables"
  es demasiado amplio para ser informativo.
- Separar `Papa criolla` de `Papa negra`, si conseguís una fuente que las distinga.

### 5.b Atajo: aplicar la receta ya escrita

En `data/openrefine/receta_homologacion.json` está una receta de **seis operaciones** lista para
aplicar: limpia espacios en `producto` y `mercado`, y agrega `es_variedad`, `producto_base`,
`permite_comparar_precio` y `confianza_mes`.

`Undo / Redo` → `Apply...` → pegá el contenido del archivo → `Perform Operations`.

**Dos cosas importantes sobre esta receta.** Primero, la escribí pero **no la ejecuté**: no tengo
OpenRefine instalado. Aplicala y revisá que las seis operaciones pasen. Segundo, aplicarla no
reemplaza los pasos 2 a 5: la receta hace lo mecánico, pero revisar las correspondencias
agregadas y genéricas producto por producto es criterio humano y es lo que el reto quiere ver.

### 6. Exportar el JSON de operaciones

`Undo / Redo` → `Extract...` → seleccioná todas las operaciones → copiá el JSON.

Guardalo en `data/openrefine/homologacion_sipsa.json`.

Ese archivo **sí se versiona**: es la evidencia del trabajo en OpenRefine y permite reaplicar
exactamente las mismas operaciones cuando el DANE publique datos nuevos, con
`Undo / Redo` → `Apply...`.

### 7. Exportar los datos

`Export` → `Comma-separated value` → guardalo como
`data/interim/sipsa/sipsa_mensual_homologado.csv`.

Ese es el archivo que entra a Power Query en la Fase 3.

---

## Parte 2 — Catálogo de artículos (448 artículos por `art_id`)

Esta parte es independiente de la homologación con FAO y es la que alimenta
`config/catalogo_articulos.csv`, el archivo que la app usa para agrupar precios.

### Por qué existe

Las fuentes nuevas (precios semanales y abastecimiento) publican **448 artículos**, no 33
productos. "Papa capira", "Papa criolla limpia" y "Papa suprema" son tres artículos distintos
del mismo producto, con precios distintos. Sin una tabla que diga cuál pertenece a cuál, la app
termina promediando variedades, que es justo lo que `docs/contrato_datos.md` prohíbe.

### El archivo de entrada y el borrador

- Entrada: `data/openrefine/catalogo_sipsa_crudo.csv` (448 artículos con `unidad_sugerida`).
- Borrador ya generado: `config/catalogo_articulos.csv`, con las columnas del contrato
  (`producto`, `grupo_dane`, `unidad`, `distingue_por`, `en_canasta`, `nota`).

**El borrador es una propuesta, no la versión final.** Lo que se revisa a mano es la asignación
de `producto` y `grupo_dane` artículo por artículo. El reto pide ver el criterio humano, y acá
es donde está.

### Las dos trampas que ya costaron un error

1. **"Papaya" empieza por "Papa".** Agrupar por la primera palabra del nombre mete las cinco
   papayas en el producto "Papa", grupo "Tubérculos". Pasó al generar el borrador y lo detectó
   `test_no_se_agrupa_por_la_primera_palabra_del_nombre` en `tests/test_app.py`.
2. **El tomate de árbol no es tomate.** Es una fruta, no una verdura, y es el artículo con más
   mercados de todo el catálogo (46).
3. **La papa criolla no es una variedad de papa: es otra especie.** La criolla es
   *Solanum phureja* y la papa común *Solanum tuberosum*. El DANE las publica aparte, y se ve en
   el propio catálogo: el abastecimiento trae dos cajones separados, `Papa criolla` (541) y
   `Papas negras otras` (498). Juntarlas haría que la mediana de «la papa» mezcle dos especies
   cuyos precios no se parecen: la criolla limpia está cerca de $4.267/kg y la parda pastusa de
   $1.700/kg. En el catálogo, `art_id` 159, 161 y 541 son producto **«Papa criolla»**.

Por eso la regla del borrador es **gana el nombre más específico**, nunca el más corto. Y, como
muestra el caso de la criolla, un nombre que *empieza* igual no garantiza el mismo producto:
hace falta saber qué publica la fuente.

### Qué separa un artículo de sus hermanos

Una vez que la criolla es su propio producto, lo que distingue «limpia» de «sucia» ya no es la
variedad sino la **presentación** — el mismo ejemplo que usa `docs/contrato_datos.md`. El
artículo 541 queda como `unico` porque el abastecimiento no separa limpia de sucia: es la
regla 7 del contrato, la correspondencia entre granularidades se declara a mano.

### Pasos en OpenRefine

1. `Create Project` → `This Computer` → `data/openrefine/catalogo_sipsa_crudo.csv`.
   Encoding `UTF-8`; verificá que `Ahuyamín (Sakata)` y `Ñame criollo` se lean bien.
2. Aplicá la receta `data/openrefine/receta_catalogo_articulos.json`
   (`Undo / Redo` → `Apply...`). Agrega columnas de apoyo: `candidato_producto`,
   `es_residual`, `es_animal_en_pie`, `en_canasta_por_presencia` y `cobertura`.
   **No la ejecuté** (no tengo OpenRefine instalado): verificá que las seis operaciones pasen.
3. Sobre `candidato_producto`: `Facet` → `Text facet` → `Cluster`, con
   `key collision` + `fingerprint` y después `nearest neighbor` + `levenshtein` radio 2.
   El clustering **propone** grupos; vos decidís. Ojo con los falsos positivos: `Papa`/`Papaya`,
   `Limón`/`Limón mandarino`, `Mora`/`Mostaza`.
4. Revisá primero los artículos con `cobertura = amplia` (los que mueven la app) y dejá para el
   final los de `cobertura = minima`.
5. Para cada grupo decidí `producto` y `grupo_dane` usando los 8 grupos oficiales de la sección
   "Jerarquía de productos y unidades" de `docs/contrato_datos.md`. Si no estás de acuerdo con el
   borrador, cambialo y escribí el motivo en `nota`.
6. `Undo / Redo` → `Extract...` → guardá el JSON en
   `data/openrefine/catalogo_articulos_revisado.json` (ese archivo se versiona).
7. `Export` → `Comma-separated value` sobre `config/catalogo_articulos.csv`, conservando solo las
   ocho columnas del contrato.

### Antes de dar por cerrado el archivo

```
..\AdquiDatos\.venv\Scripts\python.exe -m pytest tests/test_app.py -q
```

Las pruebas del catálogo fallan si queda un `art_id` repetido, un grupo que no es de los 8, una
unidad distinta de `kg`/`unidad`/`litro`, una papaya clasificada como papa, o un huevo medido
en kilos.

### Criterios del borrador, para que el equipo los acepte o los cambie

| Columna | Cómo se decidió |
|---|---|
| `producto` | Nombre más específico que coincide con el del artículo, nunca la primera palabra |
| `grupo_dane` | Los 8 grupos de la metodología SIPSA-P |
| `unidad` | `unidad_sugerida` del archivo crudo (huevo y bocadillo por unidad; aceite, jugo y vinagre por litro) |
| `distingue_por` | Qué separa al artículo de sus hermanos: `variedad`, `calidad`, `presentacion`, `origen`, `procesado` o `unico` |
| `en_canasta` | `si` si el artículo se vende en **20 mercados o más**, o si la regla del producto ya lo marcaba. Quedan fuera las categorías residuales ("Frutas otras") y los animales en pie |

---

## Si el mapeo cambia

Si editás `config/homologacion_productos.csv`, corré esto para que la validación se ejecute
contra los datos reales antes de seguir:

```bash
.venv/Scripts/python.exe scripts/preparar.py --solo sipsa
```

El validador falla si nombrás un producto que SIPSA ya no publica, si dejás un producto sin
homologar, o si usás un código de FAO que no existe para Colombia.
