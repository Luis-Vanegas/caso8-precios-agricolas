# Respuestas a las preguntas de ESTRUCTURA

Caso 8 — Predicción y detección temprana de volatilidad en precios agrícolas de Colombia.

---

## 1. ¿Cuál es el problema que se quiere resolver?

Los precios agrícolas en Colombia se mueven con una violencia que no tiene ningún activo
financiero. Medido sobre datos reales de SIPSA, el limón Tahití tiene una volatilidad anualizada
mediana del **135 %**, y una sola serie de precio en Bogotá va de 698 a 6 075 pesos por kilo:
casi nueve veces.

Esa volatilidad golpea a dos lados a la vez. Al productor, que no puede planear una siembra
cuyo precio de cosecha es impredecible. Al consumidor, que ve saltar el costo de la canasta
básica sin aviso.

El problema concreto es que **la información existe pero llega tarde y dispersa**. El DANE
publica precios mayoristas todos los días, FAO publica el contexto estructural una vez al año,
la NOAA publica el estado de El Niño cada mes, y nadie los junta. Este trabajo los junta y
señala los movimientos anómalos en el mes en que ocurren.

## 2. ¿Qué datos se necesitan y de dónde se obtienen?

| Dato | Fuente | Acceso | Frecuencia |
|---|---|---|---|
| Precio mayorista por mercado | SIPSA (DANE) | SOAP sobre HTTPS | Diaria |
| Precio al productor | FAOSTAT dominio PP | Descarga masiva | Anual y mensual |
| Producción por cultivo | FAOSTAT dominio QCL | Descarga masiva | Anual |
| Importaciones y exportaciones | FAOSTAT dominio TCL | Descarga masiva | Anual |
| Balance alimentario | FAOSTAT dominio FBS | Descarga masiva | Anual |
| Valor de la producción | FAOSTAT dominio QV | Descarga masiva | Anual |
| Tasa de cambio | FAOSTAT dominio PE | Descarga masiva | Mensual |
| Precipitación y temperatura | NASA POWER | REST sin llave | Mensual por año cerrado |
| Fase El Niño / La Niña | NOAA CPC, índice ONI | Archivo de texto | Mensual |
| Precio de fertilizantes | Pink Sheet, Banco Mundial | Excel mensual | Mensual |
| Lluvia y temperatura medidas por sensor | IDEAM, datos.gov.co | API Socrata | Cada 10 min / 1 h |

**Fuentes descartadas y por qué.** UN Comtrade, porque homologar códigos HS contra la
clasificación de FAO cuesta más de lo que aporta y FAOSTAT ya cubre comercio. EVA y UPRA, porque
solo publican Excel sin servicio. GIEWS FPMA, porque no se pudo confirmar
que tuviera API.

## 3. ¿Cómo se adquieren los datos?

Un módulo por fuente, todos con el mismo par de funciones: `estado()` dice si hay datos nuevos
sin descargar nada, y `descargar()` trae solo lo que falta. Ese contrato uniforme permite que el
orquestador las recorra en un bucle en vez de encadenar condicionales por fuente; agregar una
fuente es agregar una línea a un diccionario.

Tres mecanismos de acceso distintos:

- **FAOSTAT:** se lee el catálogo XML de descargas masivas, se compara el campo `DateUpdate` de
  cada dominio contra lo registrado en la bitácora, y se bajan solo los que cambiaron.
- **SIPSA:** POST SOAP 1.2 directo sobre HTTPS. La respuesta pesa 112 MB y se escribe a disco por
  bloques, luego se parsea con `iterparse`. Nunca se carga entera en memoria.
- **NASA POWER, ONI y Pink Sheet:** REST y archivos. La URL del Excel del Banco Mundial cambia
  cada mes, así que se descubre leyendo el HTML de la página en vez de escribirla a mano.

Todo con reintentos y espera exponencial, límite de tasa donde la fuente lo declara, y escritura
a archivo temporal que se renombra al terminar, para que una descarga cortada no quede como si
estuviera completa.

## 4. ¿Cómo se garantiza que los datos sean confiables?

Cuatro capas, en orden de cuándo actúan.

**Verificación previa.** No se escribió código contra documentación sin comprobarla contra el
servicio. Cinco supuestos resultaron falsos: la URL de la API de FAOSTAT, la autenticación, el
protocolo de SIPSA, el rango de NASA POWER y la unidad de precio de SIPSA. Cada uno habría
producido un pipeline que corre y entrega basura.

**Datos crudos inmutables.** Lo descargado se guarda tal cual en `data/raw/<fuente>/<fecha>/` y
nunca se sobrescribe. Si la limpieza tiene un error, se corrige sin volver a pedirle nada a la
fuente.

**Perfilado sistemático.** Por cada tabla se reportan nulos, únicos, rangos, duplicados por clave
y huecos de serie. Más reglas de imposibilidad: precios negativos, rangos invertidos, anomalías
ENSO fuera de rango físico, exportaciones mayores a lo disponible.

**Chequeos de integridad sobre el modelo.** Diecinueve consultas que deben devolver cero filas:
hechos que apuntan a dimensiones inexistentes, claves duplicadas, y cruces que deberían unir
algo. Si alguna devuelve filas, el script sale con error.

Además, **93 pruebas automáticas** con fixtures recortadas de respuestas reales. Ninguna toca la
red, así que corren en dos segundos, y si una fuente cambia de formato son las primeras en avisar.

## 5. ¿Cómo se integran fuentes con estructuras distintas?

Este fue el problema de fondo del trabajo, y la respuesta no fue la esperada.

SIPSA y FAOSTAT hablan idiomas distintos. SIPSA publica 33 productos con nombres comerciales
colombianos; FAOSTAT publica ítems de una clasificación internacional. Se construyó una tabla de
homologación, versionada y validada contra los datos, y el resultado fue este:

| Correspondencia | Productos | Qué significa |
|---|---:|---|
| Exacta | 13 | Mismo producto de los dos lados |
| Agregada | 10 | FAOSTAT junta varios de SIPSA en un ítem |
| Genérica | 8 | Cae en un cajón "n.e.c." |
| Sin equivalente | 2 | FAOSTAT no lo publica para Colombia |

**La correspondencia no es uno a uno**, y forzarla habría producido números falsos con apariencia
de correctos. Guayaba y mango tommy comparten el ítem 571 de FAO: su precio no corresponde a
ninguno de los dos por separado.

Por eso el modelo tiene **dos dimensiones de producto, no una**, unidas por una tabla puente que
declara en cada fila qué tan válida es la correspondencia. Solo las 13 exactas habilitan comparar
precios. Las demás sirven para ubicar el producto en la jerarquía.

Lo mismo con el clima: una zona climática sirve a varios productos de SIPSA, así que hay una
segunda tabla puente. **Esa la aprendimos por las malas.** La primera versión unía clima con
SIPSA directamente por nombre de producto. El código corría sin un solo error y unía **cero filas
de 33 977**, porque la configuración decía "Papa" y SIPSA dice "Papa negra\*". Un join que no
encuentra nada no se queja. Hoy hay un chequeo de integridad que falla si ese cruce vuelve a
quedar vacío.

## 6. ¿Qué se hace con los datos faltantes e inconsistentes?

**Se declaran, no se rellenan.** El criterio es que un hueco visible es información y un hueco
tapado es una mentira.

- **El proyecto no imputa ningún valor.** La columna `imputado` existe (hoy siempre FALSE) para
  marcarlo si algún día se interpolan huecos cortos. De las 145 series anuales de precios con
  huecos, **39** tienen huecos de más de tres años.
- SIPSA no tiene datos de enero de 2021 a enero de 2022 (13 meses). No se rellenan: los
  retornos solo se calculan entre meses consecutivos, para no inventar un "cambio mensual"
  a través del hueco.
- El centinela `-999` de NASA POWER se lee del encabezado de la respuesta y se convierte a nulo.
  Sin ese paso entra como si fuera una temperatura.
- Un consumo aparente nulo o negativo no produce porcentaje de dependencia: se deja vacío en vez
  de generar un número que parezca válido.
- Sin observaciones suficientes no hay alerta. Decir "verde" con tres meses de historia sería
  afirmar que algo está bien cuando en realidad no se sabe.

**Las inconsistencias se investigan antes de contarlas.** El chequeo de comercio imposible arrojó
2 730 casos. Al abrir el primero resultó ser `Fruit`, que es un agregado de grupo sin producción
primaria. Filtrando a ítems comparables y a una sola unidad quedaron 97, y de esos solo **9 son
inconsistencias reales**; las otras 88 son años que la fuente aún no publicó. De 2 730 a 9.

## 7. ¿Cómo se actualizan los datos?

```bash
.venv/Scripts/python.exe scripts/actualizar.py     # descarga solo lo nuevo
.venv/Scripts/python.exe scripts/preparar.py       # limpia y perfila
.venv/Scripts/python.exe scripts/integrar.py       # carga el modelo y verifica
```

Los tres son **idempotentes**: una segunda corrida seguida deja todas las fuentes en caché sin
descargar un byte. Está verificado, no asumido.

Cada fuente se compara contra la bitácora `meta_actualizacion`, que guarda por descarga la fecha,
el último periodo con dato, la fecha que reporta la fuente y el estado. Esa misma tabla alimenta
el panel de frescura de la app.

Calendario: SIPSA diario a las 2 p.m., SIPSA mensual el día 8, ONI el segundo jueves, Pink Sheet
a comienzo de mes, FAOSTAT una vez al año. NASA POWER mensual va por años cerrados con más de un
año de rezago.

## 8. ¿Cómo se presenta el resultado?

Una app en Streamlit con siete páginas, que lee del archivo DuckDB versionado y **nunca llama a
las APIs en vivo**. Es una decisión, no una limitación: si una fuente se cae, la app sigue
funcionando y el panel de frescura dice qué tan viejo es cada dato.

La página que más importa no es el semáforo, es **Calidad de datos**, porque un dato sin su
limitación declarada es un dato peligroso. Ahí está el conteo de homologaciones, los ítems de
FAOSTAT que reciben varios productos, y las siete limitaciones de las fuentes.

Y en el detalle de cada producto, cuando la correspondencia no es exacta, la app **advierte
explícitamente** que comparar los dos precios produciría un margen inventado. La limitación viaja
con el dato, no queda escondida en un anexo.

## 9. ¿Qué no se puede concluir con estos datos?

- **No se puede calcular un margen de intermediación.** Los precios al productor de FAOSTAT para
  Colombia son cifra oficial del gobierno colombiano, probablemente del mismo sistema del DANE
  que alimenta SIPSA. Las dos series no son independientes.
- **No se puede comparar precios de 20 de los 33 productos** entre las dos fuentes.
- **No se puede caracterizar el clima de un municipio** con NASA POWER: la grilla promedia el
  relieve y a Villavicencio, que está a 467 m, le asigna 1 392 m.
- **No está comprobado que las alertas anticipen crisis de abastecimiento.** Detectan movimientos
  estadísticamente anómalos, que es otra cosa. Validar eso requiere una lista de eventos
  conocidos contra la cual medir, y ese es el siguiente trabajo.
