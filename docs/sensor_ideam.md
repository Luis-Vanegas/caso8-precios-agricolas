# Kit del sensor IDEAM (material de estudio para la sustentación)

Es material para estudiar y tener a mano. **No es texto para el informe** (la guía AE2 prohíbe texto de IA en el informe): úsenlo para entender y luego explíquenlo con sus palabras.

Leyenda: **[V]** = verificado contra la fuente real o contra la base. **[R]** = referencia de diseño, no confirmado para el equipo del IDEAM. **[?]** = pendiente de comprobar.

---

## 1. Qué mide

Lluvia, en milímetros (mm). 1 mm de lluvia es 1 litro de agua por metro cuadrado. Es la fuente de tipo **sensor** del proyecto: cada fila es la lectura de un sensor físico en una estación con código, municipio y coordenadas. **[V]** (dataset `s54a-sgyg`, unidad `mm`).

Lo que NO hace: no mide temperatura en la app. El dataset de temperatura (`sbwg-7ju4`) está verificado pero no se descargó. **[V]**

## 2. Cómo funciona un pluviómetro de balancín **[R]**

1. La lluvia entra por un embudo y cae en una de dos cubetas montadas en un balancín (como un sube y baja).
2. Cuando la cubeta recoge cierta cantidad de agua (en el diseño de referencia, **0,1 mm** de lluvia), se inclina por el peso, el balancín vuelca y la otra cubeta queda debajo del embudo.
3. Un imán pegado al balancín pasa frente a un interruptor de lengüeta (**reed switch**) y lo cierra un instante: eso es **un pulso eléctrico**.
4. Un contador suma pulsos. Lluvia (mm) = pulsos × 0,1.

El modelo de referencia que usamos para explicarlo es el **Texas Electronics TE525MM** (0,1 mm por vuelco, salida por reed switch). **[R]** `docs/verificacion_api.md` dice textualmente que NO es el modelo confirmado del IDEAM, y `docs/plan_equipo.md` pide verificar sus datos en la hoja técnica: yo no pude abrir la ficha del TE525MM en la web del fabricante (el enlace de producto dio 404), así que esos datos hay que leerlos de la hoja técnica antes de la sustentación.

## 3. La cuenta de los 11 bits

El deck dice: rango 0–200 mm, resolución 0,1 mm, 11 bits. La cuenta cuadra:

- Intervalos: 200 mm ÷ 0,1 mm = **2.000** (son 2.001 valores posibles si se cuenta el 0,0 y el 200,0).
- Con *n* bits se distinguen 2^n valores: 2^10 = 1.024 (**no alcanza**) y 2^11 = **2.048** (sí alcanza, sobran 47).
- Por eso 11 bits. Con 12 bits (4.096) sobraría el doble; con 11 es el mínimo entero que sirve.

Cuidado con la lectura del número: los 11 bits son una decisión de **diseño** del ejemplo del deck. **[R]** Que el rango 0–200 mm sea por lectura de 10 minutos es un rango de diseño del conversor, no algo medido en los datos (en 10 minutos casi nunca caen 200 mm). Los docs atribuyen la resolución y el rango a WMO-No. 8 (2023), vol. I, cap. 6 y anexo 1.A, pero **[?]** nadie del equipo ha contrastado esas cifras con el texto de la OMM: léanlo antes de afirmarlo con seguridad.

## 4. La cadena de adquisición de datos (DAQ)

DAQ = *Data AcQuisition*. Es el camino de una magnitud física hasta ser dato:

| # | Paso | Qué pasa | Estado |
|---|---|---|---|
| 1 | Fenómeno | Cae lluvia | — |
| 2 | Transductor | Balancín + reed switch: lluvia → pulso eléctrico | [R] |
| 3 | Acondicionamiento y conteo | Se cuentan los pulsos (cada uno = 0,1 mm) | [R] |
| 4 | Digitalización | 2.000 niveles → 11 bits | [R] |
| 5 | Registro en la estación | Un valor cada 10 min (convencional `0240`) | [V] |
| 6 | Transmisión | Convencional (10 min) o GPRS `0257` (~2 min) | [V] |
| 7 | Publicación | datos.gov.co, API Socrata, dataset `s54a-sgyg` | [V] |
| 8 | Nuestro pipeline | SoQL agrega por mes en el servidor → limpieza → DuckDB | [V] |

La app lo muestra en la página **Sensor IDEAM**, sección "La cadena de adquisición".

## 5. De dónde sale cada dato **[V]**

- **Dataset:** Precipitación, `s54a-sgyg`, Datos Abiertos Colombia, atribuido al IDEAM. Ficha: <https://www.datos.gov.co/d/s54a-sgyg>. API: `https://www.datos.gov.co/resource/s54a-sgyg.json`.
- **Tamaño** (verificado el 2026-09-22): 165 294 457 filas, 116 312 104 con valor.
- **Última lectura vista:** 2026-09-21T23:59.
- **Columnas:** `codigoestacion`, `codigosensor`, `fechaobservacion`, `valorobservado`, `nombreestacion`, `departamento`, `municipio`, `zonahidrografica`, `latitud`, `longitud`, `descripcionsensor`, `unidadmedida`.
- **Códigos de sensor de lluvia y su frecuencia real** (mediana del intervalo, estación `0024035340`):

| Código | Descripción | Intervalo mediano |
|---|---|---|
| `0240` | PRECIPITACIÓN (convencional) | 10 min (coincide con la ficha) |
| `0257` | GPRS - PRECIPITACIÓN | ~2 min (no documentado en la ficha) |

  (Para temperatura: `0068` convencional cada 60 min y `0071` GPRS cada ~2 min.)
- **Control de calidad:** el IDEAM declara control básico según recomendaciones de la OMM (ficha del dataset).
- En la base: **450 estaciones** (441 con sensor `0240`, 9 con `0257`), 8 departamentos, 600 filas departamento-mes, de 2020-01 a 2026-09 (Quindío llega a 2026-07).

Muestras reales guardadas para la app: `app/ejemplos/ideam_lectura_cruda_sensor.json` (dos lecturas crudas) y `app/ejemplos/ideam_agregado_estacion_mes.json` (la estación Cajamarca, Tolima, julio de 2026: suma 53,0 mm, 5.390 lecturas, máximo 2,5).

## 6. Cómo lo bajamos y por qué así

- **No se baja el crudo.** Son ~116 millones de lecturas con valor. Se le pide al servidor que agregue con **SoQL** (el lenguaje de consulta de Socrata): suma, promedio, mínimo, máximo y conteo, agrupado por estación, sensor y mes.
- **Por qué en el servidor:** descargar 116 M de filas sería lento, enorme y sin necesidad: solo nos importa la lluvia acumulada del mes.
- **Un mes por llamada.** Verificado con `scripts/probe_ideam.py`: el año completo, el semestre y hasta el trimestre dan **timeout** (200–300 s) en los departamentos grandes (Boyacá ~1,6 M lecturas en 2026). Por mes responde en 15–30 s. El cuello de botella es el volumen agregado, no el número de columnas del `$group` ni el índice.
- **Ventanas de 5 días** para los meses que aun así dan timeout: Cundinamarca dic-2024 y ene-2025. Se piden 5 días por vez y se combinan: las sumas y los conteos se **suman**; el mínimo y el máximo se **recalculan** (no se promedian).
- **Trampa de mayúsculas:** cada departamento aparece dos veces, `BOYACÁ` y `Boyacá`, repartiéndose el tiempo (sin meses en común), porque el IDEAM cambió de convención a mitad de 2026. Se piden ambas variantes por igualdad exacta (con `upper()` se rompe el índice y da timeout) y la limpieza las unifica con `a_vocabulario_config`. Antes de arreglarlo el código perdía en silencio hasta ~85 % de las lecturas de Boyacá.
- **Un typo que daba cero filas:** `Norte De Santander` (con "De" mayúscula) y no `de`.
- **Sensores por separado:** se agrupa también por `codigosensor`; una estación puede tener convencional y GPRS y sumarlos contaría la lluvia dos veces.
- **Token:** opcional (`X-App-Token`, variable `SOCRATA_APP_TOKEN`). Sin token funciona con límite de tasa.
- **Resultado:** descarga del 29-sep-2026, 387 063 registros.

## 7. Dónde está en el código

| Qué | Archivo y función |
|---|---|
| Consulta SoQL mensual | `src/acquisition/ideam.py` → `consulta_mensual()` |
| Recorrer meses y variantes de mayúsculas | `ideam.py` → `_paginas()` |
| Bajar y guardar el crudo | `ideam.py` → `descargar()` (a `data/raw/ideam/<fecha>/`) |
| Muestra de lecturas crudas | `ideam.py` → `consulta_muestra()` y `_guardar_muestra()` |
| Frescura de la fuente | `ideam.py` → `estado()` y `fecha_actualizacion()` (`rowsUpdatedAt`) |
| Pruebas de las suposiciones | `scripts/probe_ideam.py`; `tests/test_ideam.py` |
| Limpieza por estación | `src/cleaning/ideam.py` → `leer()`, `limpiar()` (completitud ≥ 0,8, rango físico) |
| Mediana por departamento y anomalía | `src/cleaning/ideam.py` → `a_departamento()` |
| Tablas del modelo | `src/integration/modelo.py` → `dim_estacion_ideam`, `fact_sensor_ideam` |
| Página de la app | `app/secciones/sensor.py` (pestaña "Sensor IDEAM" de la página Clima) |

Decisiones de limpieza para defender: **completitud relativa** (cada mes contra la mediana de lecturas de esa misma estación y sensor, mínimo 0,8), **rango físico** (lluvia negativa = falla del sensor, se marca, no se corrige) y **mediana entre estaciones** (una estación descalibrada no arrastra al departamento como lo haría un promedio).

## 8. Cómo mostrarlo en la demo (60–90 segundos)

Abrir la app → menú **Cómo lo hicimos → Sensor IDEAM**.

1. **(15 s) Cadena DAQ.** Señalar las 8 tarjetas de izquierda a derecha: "la lluvia vuelca un balancín, eso es un pulso, se digitaliza en 11 bits, la estación registra cada 10 minutos, se publica en datos.gov.co y nosotros lo agregamos por mes". Decir la frase: "los pasos 2 a 4 son una referencia de diseño; del 5 en adelante está verificado".
2. **(10 s) Contadores.** "450 estaciones, 8 departamentos, 78 meses."
3. **(20 s) Mapa.** "Cada punto es una estación; los cuadrados oscuros son las plazas donde miramos precios. Así vemos dónde se mide la lluvia y dónde se vende." Pasar el mouse por una estación para mostrar código y porcentaje de meses válidos.
4. **(20 s) "Así llega un dato".** Mostrar el JSON crudo, luego el agregado de Cajamarca (53 mm en julio, 5.390 lecturas) y la fila del Tolima (14,15 mm, mediana de 26 estaciones): "de millones de lecturas a una fila".
5. **(10 s) Gráfica mensual.** Elegir un departamento y señalar una barra azul y una café.
6. **(5 s) Limitaciones.** "Solo lluvia; hay meses sin dato (Meta: 69 de 81) y se declaran."

Si algo falla en vivo: la app lee de DuckDB, no de la API; no depende de internet para las cifras (solo las letras de Google Fonts).

## 9. Preguntas probables del jurado

**1. ¿Por qué 11 bits?** Porque 0–200 mm con paso de 0,1 mm son 2.000 niveles; 10 bits dan 1.024 y no alcanzan, 11 bits dan 2.048 y sí. Es un diseño de referencia, no el conversor del IDEAM.

**2. ¿Ese pluviómetro es el que usa el IDEAM?** No lo sabemos. Es una referencia de diseño (TE525MM). Lo verificado es el dataset, sus columnas, los códigos de sensor y las frecuencias.

**3. ¿Por qué no bajaron todos los datos y los procesaron acá?** Son ~116 millones de lecturas con valor. Solo necesitamos la lluvia acumulada por mes, así que el servidor la suma (SoQL) y bajamos unos cientos de miles de registros.

**4. ¿Por qué un mes por consulta?** Porque año, semestre y trimestre dieron timeout (lo probamos en `scripts/probe_ideam.py`). Por mes responde en 15–30 s. Dos meses de Cundinamarca necesitaron ventanas de 5 días.

**5. ¿Cómo saben que los datos son confiables?** El IDEAM declara control básico según la OMM. Nosotros marcamos meses con menos del 80 % de las lecturas típicas de la estación y lluvias negativas, y usamos la mediana entre estaciones para que una mala no arrastre al departamento.

**6. ¿Por qué hay estaciones con sensor `0257` y otras `0240`? ¿Se suman?** `0240` es convencional (cada 10 min) y `0257` es GPRS (cada ~2 min). No se suman: se agrupan por código de sensor para no contar la lluvia dos veces.

**7. ¿Qué pasa con los huecos?** Se declaran, no se rellenan. Meta tiene 69 de 81 meses con dato; Quindío llega a julio de 2026; Cundinamarca 2024–2025 y Antioquia se completaron con ventanas de 5 días.

**8. ¿Qué tiene que ver la lluvia con los precios?** Es una pista, no una predicción: en la lista de vigilancia se busca qué productos se han movido junto con la lluvia de 1 a 3 meses antes en su zona productora (hay otra fuente de clima, NASA POWER, para esto). Una correlación no demuestra causa.

**9. (Difícil) Una estación de 10 minutos debería tener unas 4.464 lecturas en un mes de 31 días, pero Cajamarca tiene 5.390. ¿Por qué?** **[?]** No lo hemos investigado. Observación honesta: varias estaciones convencionales del Tolima en julio de 2026 muestran entre ~5.400 y ~5.600 lecturas (otras, como Purificación, 4.723), más de las 4.464 esperadas con un intervalo estricto de 10 min. Puede deberse a lecturas adicionales o a intervalos irregulares; no lo verificamos, y por eso la limpieza compara cada mes contra la mediana de la propia estación y no contra un número fijo.
