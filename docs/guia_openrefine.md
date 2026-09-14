# Guía de OpenRefine — homologación de productos

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

## Si el mapeo cambia

Si editás `config/homologacion_productos.csv`, corré esto para que la validación se ejecute
contra los datos reales antes de seguir:

```bash
.venv/Scripts/python.exe scripts/preparar.py --solo sipsa
```

El validador falla si nombrás un producto que SIPSA ya no publica, si dejás un producto sin
homologar, o si usás un código de FAO que no existe para Colombia.
