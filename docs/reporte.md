# Reporte del proceso — Caso 8

**Predicción y detección temprana de volatilidad en precios agrícolas de Colombia**

Adquisición e Integración de Datos — Ingeniería en Ciencia de Datos, ITM.
Datos actualizados al 15 de septiembre de 2026.

---

## 1. Qué se construyó

Un pipeline reproducible que integra **cinco fuentes** en una base analítica, más una app de
demostración que señala movimientos anómalos de precio en los mercados mayoristas del país.

| Fuente | Rol | Acceso | Filas de Colombia |
|---|---|---|---:|
| SIPSA (DANE) | Precios mayoristas diarios por mercado | SOAP | 383 718 |
| FAOSTAT | Producción, comercio, balances, valor, precios, tasa de cambio | Bulk + API | 159 082 |
| NASA POWER | Precipitación y temperatura en zonas productoras | REST | 3 780 |
| ONI (NOAA CPC) | Fase El Niño / La Niña | Texto plano | 919 |
| Pink Sheet (Banco Mundial) | Precios de fertilizantes y combustibles | Excel mensual | 50 383 |

La base resultante tiene **18 tablas** y **249 563 filas** en un archivo DuckDB de 5,8 MB, que
se versiona en el repositorio para que la app funcione sin credenciales.

## 2. Las tres herramientas del reto

| Herramienta | Qué hace acá | Evidencia |
|---|---|---|
| **Python** | Adquisición, perfilado, limpieza, indicadores y carga | `src/`, `scripts/`, 75 tests |
| **OpenRefine** | Homologación de los 33 productos de SIPSA | `data/openrefine/`, `docs/guia_openrefine.md` |
| **Power Query** | Integración en tabla analítica única | `powerquery/*.pq`, `docs/guia_powerquery.md` |

Flujo: Python lleva de crudo a intermedio, OpenRefine homologa, Power Query integra, DuckDB
almacena, Streamlit presenta.

## 3. El método: verificar antes de escribir

La regla de trabajo fue no escribir una línea de código contra documentación sin comprobarla
contra el servicio real. Eso cambió cinco decisiones de diseño.

### 3.1 La API de FAOSTAT exige token, y la otra URL está muerta

La documentación disponible daba dos URL base y se contradecía sobre la autenticación. Probadas
las dos: `faostatservices.fao.org` responde **401** con el cuerpo `Missing Authorization Header`,
y `fenixservices.fao.org` responde **521**, servidor de origen caído.

Como la carga histórica sale de las descargas masivas, que no piden credenciales, el proyecto no
quedó bloqueado. Si nos hubiéramos apoyado en la API sin probar, sí.

### 3.2 SIPSA no funciona como dice su documentación

La guía del DANE es de 2020 y declara un endpoint HTTP. Ese endpoint **no procesa SOAP**:
responde la página informativa de JAX-WS a cualquier petición, con lo cual el cliente `zeep`
falla con un error de XML que no dice nada útil.

El mismo servicio **por HTTPS sí responde**, y el binding es **SOAP 1.2**, no 1.1. Dos
correcciones que no están escritas en ningún lado y solo aparecen probando.

También se verificó que `promediosSipsaCiudad` es **idempotente**: dos llamadas devolvieron
exactamente los mismos 383 545 registros. Eso descartó el riesgo, documentado en la guía, de que
el servicio entregue solo registros no consultados antes.

### 3.3 NASA POWER mensual va por años completos, no por meses cerrados

El supuesto inicial era pedir hasta el último mes cerrado, porque el servicio publica con dos o
tres días de rezago. **Eso vale para el endpoint diario, no para el mensual.** Pedir el año en
curso devuelve 422 con el mensaje `The data is available to 2025/12/31`.

El servicio publica su propio límite en `/configuration`, así que el código lo lee de ahí en vez
de estimarlo con la fecha del sistema.

### 3.4 La unidad de precio de SIPSA quedó confirmada por triangulación

La guía del DANE describe `promedioKg` como una cantidad, pero los valores solo tienen sentido
como precio. Se confirmó comparando contra FAOSTAT, que publica en pesos por tonelada:

| Producto | Año | FAOSTAT (COP/kg) | SIPSA (COP/kg) | Diferencia |
|---|---:|---:|---:|---:|
| Papa | 2022 | 1 964,7 | 2 012 | 2,4 % |
| Tomate | 2022 | 2 661,7 | 2 657 | 0,2 % |

Dos fuentes dentro del 3 % confirman la unidad. La suposición se volvió dato verificado.

### 3.5 Un carácter raro en pantalla no siempre es un dato corrupto

Durante la limpieza apareció `SAN JOS? DE C?CUTA`. Antes de tocar nada se revisó el ordinal del
carácter: 193, que es `Á`. El dato estaba perfecto y lo que fallaba era la consola de Windows.
"Arreglarlo" habría corrompido datos sanos.

## 4. Los tres hallazgos que cambian el análisis

### 4.1 SIPSA y FAOSTAT no se pueden cruzar producto a producto

De los 33 productos de SIPSA, solo **13 tienen correspondencia exacta** con un ítem de FAOSTAT.

| Tipo de correspondencia | Productos |
|---|---:|
| Exacta | 13 |
| Agregada (FAO junta varios en un ítem) | 10 |
| Genérica (cae en un cajón "n.e.c.") | 8 |
| Sin equivalente en FAOSTAT | 2 |

Seis ítems de FAOSTAT reciben más de un producto de SIPSA. Guayaba y mango tommy comparten el
ítem 571; limón común y limón Tahití comparten el 497; granadilla, lulo, maracuyá y tomate de
árbol caen los cuatro en "Other tropical fruits, n.e.c.".

**Consecuencia:** el precio productor del ítem 571 no es el de la guayaba ni el del mango, es una
mezcla. Comparar contra él produce un margen inventado que se ve perfectamente razonable en un
gráfico.

Se verificó además que la granularidad **no existe en ningún dominio** de FAOSTAT: "Passion
fruit", "Blackberry", "Tree tomato", "Lulo" y "Granadilla" no aparecen en precios, ni en
producción, ni en comercio. No es un problema de acceso que otra API resuelva; es el límite de
una clasificación internacional que no contempla productos andinos.

### 4.2 Para precios, las dos fuentes no son independientes

Los precios convertidos de FAOSTAT y los de SIPSA coinciden dentro del 3 %. Eso es sospechoso en
la dirección contraria: un precio mayorista debería estar **por encima** del precio al productor,
porque entre los dos hay transporte, acopio e intermediación.

Los 6 893 registros de precio al productor de Colombia llevan flag `A`, "cifra oficial", o sea
que FAO los recibe del gobierno colombiano. Lo más probable es que ambas series salgan del mismo
sistema de captura del DANE.

**Por eso la razón entre los dos precios no se presenta como margen de intermediación.** Sirve
como validación cruzada de unidades y consistencia, y así está etiquetada en la base y en la app.

### 4.3 La grilla de NASA POWER deforma el clima en terreno montañoso

POWER devuelve la elevación que asigna a su celda de grilla. En Colombia difiere mucho de la real:

| Zona | Elevación real | Elevación de la celda |
|---|---:|---:|
| Villavicencio, Meta | 467 m | 1 392 m |
| Bogotá, Cundinamarca | 2 640 m | 1 790 m |

La serie climática no es el clima del municipio, es el promedio de una celda que mezcla valle y
montaña. Por eso el indicador de contexto usa **anomalías** y no valores absolutos: la anomalía
compara cada mes contra el promedio histórico del mismo mes en la misma celda, y el sesgo de
elevación se cancela.

## 5. Tratamiento de faltantes e inconsistencias

### Inconsistencias de comercio

El chequeo de "exportaciones mayores a producción más importaciones" arrojó inicialmente **2 730
casos**. Al abrir el primero apareció `Fruit` con producción cero. `Fruit` no es un cultivo, es un
agregado de grupo que FAOSTAT publica en comercio y no en producción. Lo mismo `Apple juice`, que
es un procesado.

Con dos filtros, comparar solo ítems presentes en ambos dominios y solo en toneladas, quedaron
**97 casos**. De esos, **88 tienen producción en cero**, o sea que la fuente no publicó ese año,
y **9 son inconsistencias reales**. La mayor: café verde en 2021, con 687 866 toneladas
exportadas contra 663 144 disponibles.

De 2 730 a 9. La diferencia fue abrir el dato en vez de confiar en el agregado.

### Faltantes

- Las series anuales de precios tienen **145 con huecos**; **39** con huecos de más de tres años,
  que no se interpolan y se dejan vacías.
- El valor centinela `-999` de NASA POWER se lee del encabezado de la respuesta y se convierte a
  nulo. Sin ese paso entra como si fuera una temperatura y arruina cualquier promedio.
- El consumo aparente nulo o negativo no produce porcentaje de dependencia: se deja vacío en vez
  de generar un número que parezca válido.
- Cada mes de SIPSA lleva `dias_con_dato`. Un mes con dos días no vale lo mismo que uno con veinte.

## 6. El indicador de alerta

Sobre precios mayoristas mensuales de SIPSA:

1. **Retorno logarítmico** mes a mes. Se usa logaritmo y no variación porcentual porque es
   simétrico: subir al doble y volver a la mitad se cancelan exactamente. En porcentaje no, y eso
   sesga cualquier promedio posterior.
2. **Volatilidad**: desviación estándar móvil de 12 meses, anualizada. Mínimo 6 observaciones.
3. **Alerta**: z-score del retorno del mes contra la historia previa de esa misma serie. Amarilla
   sobre 2 desviaciones, roja sobre 3. **Los umbrales son convenciones de este trabajo, no
   estándares oficiales.**

El z-score se calcula con ventana expansiva, que usa solo pasado y presente. Usar la media de
toda la serie filtraría información que en su momento no existía y volvería el indicador inútil
en vivo. Hay un test que lo verifica.

**Por qué sobre SIPSA y no sobre FAOSTAT.** La detección temprana necesita frecuencia. SIPSA
publica a diario y el 89 % de sus 589 series tiene 24 meses o más de historia. FAOSTAT publica
una vez al año con un año de rezago: aporta contexto estructural, no señal temprana.

## 7. Fortalezas y debilidades

### Fortalezas

- **Nada se dio por cierto sin verificar.** Cinco supuestos de la documentación resultaron falsos
  y se corrigieron contra el servicio real.
- **Idempotencia probada.** Una segunda corrida completa deja todas las fuentes en caché sin
  descargar un byte.
- **Las limitaciones están en los datos, no solo en el texto.** La elevación de grilla es una
  columna; el tipo de correspondencia viaja con cada fila; la app muestra una advertencia cuando
  el producto no admite comparación.
- **75 tests, ninguno toca la red.** Las fixtures son recortes de respuestas reales, así que si
  una fuente cambia de formato, los tests avisan.
- **19 chequeos de integridad** sobre el modelo, tres de los cuales nacieron de un error real.

### Debilidades

- **La API REST de FAOSTAT quedó sin verificar** por falta de token. El esquema de autenticación
  y las rutas están marcados `TODO VERIFICAR`.
- **Las zonas productoras son capitales departamentales** usadas como aproximación. Faltan los
  polígonos de producción de UPRA/EVA.
- **El servicio web de SIPSA arranca en febrero de 2020.** Para historia más larga hay que sumar
  los microdatos del DANE de 2013 a 2024.
- **Los métodos `*Madr` de SIPSA no se probaron**, porque pueden entregar solo registros no
  consultados antes y una llamada mal hecha quemaría datos irrecuperables.
- **Solo 13 de 33 productos** admiten comparación de precios entre fuentes. Es un resultado, no
  un defecto, pero limita el alcance del cruce.
- **Las alertas no fueron validadas contra eventos conocidos.** Se sabe que detectan movimientos
  estadísticamente anómalos; no está comprobado que anticipen crisis de abastecimiento.

## 8. Cómo actualizar los datos

```bash
.venv/Scripts/python.exe scripts/actualizar.py     # descarga solo lo nuevo
.venv/Scripts/python.exe scripts/preparar.py       # limpia y perfila
.venv/Scripts/python.exe scripts/integrar.py       # carga el modelo y verifica
```

Los tres son idempotentes. `actualizar.py` acepta `--solo <fuente>` y `--dry-run`.

**Cerrá la app de Streamlit antes de actualizar:** mantiene el archivo DuckDB abierto y en
Windows eso bloquea la escritura.

Calendario de publicación de cada fuente y checklist previo a la entrega: `docs/perfilado.md` y
la página "Calidad de datos" de la app.
