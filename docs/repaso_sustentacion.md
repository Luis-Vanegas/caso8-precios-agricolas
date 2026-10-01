# Repaso para la sustentación — todo explicado fácil

Cifras revisadas el 1-oct-2026 contra la base real (`caso8.duckdb`) y contra las diapositivas.
Cada "Frase para decir" es una idea corta; díganla con sus palabras.

---

## 0. El proyecto en 20 segundos
"Los precios de los alimentos en las plazas mayoristas se disparan sin aviso. Los datos para anticiparlo existen,
pero están en seis fuentes distintas que no se hablan. Las juntamos en una sola base y una app que avisa cuando un
precio se mueve de forma rara."

## 1. Cómo se hizo: la receta del sancocho
| Paso | Qué es (fácil) | Qué lo hace |
|---|---|---|
| 1. Conseguir | Pedir los datos a cada fuente y guardarlos **sin tocarlos** | `scripts/actualizar.py` → `data/raw/` |
| 2. Limpiar | Mismo formato y **un dato por mes** (SIPSA trae un precio por día) | `scripts/preparar.py` → `data/interim/` |
| 3. Homologar | Que "Papa negra*" (SIPSA) y "Potatoes" (FAO) se reconozcan como lo mismo | `config/homologacion_productos.csv`, revisada con **OpenRefine** |
| 4. Unir | Todo en una base ordenada (**modelo estrella** en DuckDB) y **19 chequeos** de calidad | `scripts/integrar.py` |
| 5. Detectar | Calcular qué tan raro fue el cambio de cada precio | `src/indicators/volatilidad.py` |
| 6. Mostrar | La app lee la base; no llama a las APIs en vivo | `app/streamlit_app.py` |

**¿Es fácil para una persona?** Por partes:
- **Power Query y OpenRefine:** sí. Son clics; con la guía se hace en menos de una hora.
- **Python (pedir, limpiar, agrupar):** accesible: son `requests`, `groupby` y `merge`, comentados línea por línea.
- **Lo difícil no era el código, sino las trampas** que se encontraron *verificando contra la fuente real*:
  SIPSA solo responde por HTTPS y SOAP 1.2; el IDEAM escribe cada departamento de dos formas (`BOYACÁ` y `Boyacá`);
  SIPSA no tiene datos de 2021; NASA promedia el relieve.
- Sean honestos: el sistema se construyó **con ayuda de IA** y ustedes lo revisaron. Lo que cuenta es que cada uno
  pueda explicar qué hace cada parte y por qué. Si no pueden explicar algo, no lo defiendan: digan "eso lo hace X, lo que sé es...".

## 2. Power Query, explicado
**Qué es:** la herramienta de Excel (y Power BI) para traer, limpiar y **unir tablas con clics**. Cada clic escribe una
línea de código (lenguaje M) que queda guardada y se puede repetir al actualizar los datos.

**La idea de unir tablas:** para juntar dos tablas hace falta una columna en común, como la **cédula** en dos bases de
datos. Aquí hay tres llaves: **producto**, **departamento** y **año-mes**.

**Ejercicio de práctica (`Ejercicio_PowerQuery/`), 4 pasos:**
1. **Cargar los 4 CSV** (precios, zonas, lluvia, El Niño). Importante: codificación UTF-8, o se rompen las tildes y la unión por producto no encuentra nada.
2. **Precios + zonas** (por `producto`, unión interna): pasa de **6.842 a 8.906 filas**. ¿Por qué *más*? Porque la **papa tiene dos zonas** (Boyacá y Cundinamarca) y cada precio de papa sale dos veces. Es una relación **uno a muchos**.
3. **+ Lluvia del sensor** (por `departamento` **y** `periodo`, unión **externa izquierda**).
4. **+ El Niño** (por `anio` **y** `mes`, externa izquierda). Se carga como `BaseIntegrada`.

**Comprobación (verificada):** 8.906 filas · 8.250 con lluvia · 8.638 con fase de El Niño · 7 productos · 20 mercados.

**Dos decisiones que te pueden preguntar:**
- *¿Por qué unión externa izquierda?* Para **no perder ningún precio** aunque ese mes no haya lluvia: el hueco se deja visible, no se rellena.
- *¿Por qué una tabla puente?* La configuración dice "Papa" y SIPSA dice "Papa negra*". Unir directo por el nombre **corre sin error y devuelve cero filas**: un join vacío no se queja. La puente traduce entre los dos vocabularios.

**La versión completa del proyecto** está en `powerquery/` (7 consultas: parámetros, SIPSA, FAOSTAT, ONI, clima, zonas y `03_BaseIntegrada`). Hace lo mismo que `integrar.py` en Python, pero con clics. El parámetro `CarpetaProyecto` tiene una ruta de tu computador; en otro PC hay que cambiarla.

**Frase para decir:** "Hicimos la integración dos veces: en Python/DuckDB para el sistema, y en Power Query para demostrar que la misma lógica se puede hacer con clics. Las dos dan el mismo resultado."

## 3. La alerta: z-score en palabras simples
**Idea:** subir de precio no es raro (la papa sube y baja todo el tiempo). Lo raro es que **este mes** cambió mucho
**más de lo que ese producto suele cambiar en ese mercado**.

1. **Cambio del mes:** se calcula el retorno logarítmico `r = ln(precio hoy / precio mes anterior)`. Se usa logaritmo porque es simétrico: subir 50 % (+0,405) y bajar 33 % (−0,405) se compensan.
2. **Qué es normal:** el promedio y la desviación de los cambios *anteriores* de esa misma serie. Solo se mira el **pasado** (`expanding`), nunca el futuro. Mínimo 6 meses de historia.
3. **z-score:** a cuántas desviaciones quedó este cambio de lo normal.
4. **Semáforo:** |z| > 2 → **amarilla**; |z| > 3 → **roja**. **Los umbrales los pusimos nosotros; no son un estándar oficial.**
5. **Volatilidad anualizada:** desviación de los cambios de 12 meses × √12. El limón Tahití tiene **135 %** (mediana).

*(Ejemplo inventado solo para entender: si un producto cambia casi siempre entre −5 % y +5 % y un mes sube 30 %, queda muy lejos de lo normal → alerta roja.)*

**Detalles que muestran que entienden:** no se calcula el cambio entre meses que no son consecutivos (el hueco de 2021 corta la serie); sin z-score no hay alerta (no se dice "verde" si no se sabe); un producto muy volátil dispara pocas alertas porque para él los saltos grandes son normales.

## 4. La app, página por página
| Página | Qué muestra | Cómo se lee | Frase para decir |
|---|---|---|---|
| **Inicio** | Cuántas series vigila, alertas rojas/amarillas del último mes **cerrado**, mapa de mercados, tarjetas de las 6 fuentes, aviso si hay El Niño | Punto rojo/amarillo = mercado con alertas; más grande = más productos con alerta | "Esta es la portada: qué está pasando este mes en una pantalla." |
| **Lo que va de 2026** | Izq.: cambio de precio **frente al mismo mes del año pasado** por producto (rojo más caro, azul más barato). Der.: alertas por mes. Abajo: El Niño del año | Se compara con el mismo mes porque muchos alimentos son de temporada | "Es análisis con datos nuevos: se actualiza solo al correr el pipeline." |
| **Semáforo de alertas** | Tabla de series que se salieron de lo normal en el mes elegido; mapa; barras de volatilidad por producto | Cada fila = un producto en un mercado; el z-score dice qué tan raro fue | "Compara cada serie contra su propia historia: no importa si es caro, importa si se movió distinto." |
| **Detalle por producto** | Línea de precio con banda mín–máx, círculos de alerta, barras de z-score, comparación con FAO | Barra en la franja amarilla/roja = cambio raro; hueco = mes sin dato (2021) | "Aquí se ve la historia de un producto en un mercado." |
| **Recorrido paso a paso** | Explica el pipeline con datos reales de antes y después | De arriba abajo: conseguir → limpiar → homologar → unir → detectar | "Es el tutorial del sistema." |
| **Sensor IDEAM** | Cadena DAQ, mapa de estaciones y mercados, dato crudo → agregado → fila | Barra azul = llovió más que lo normal del mes; café = menos | "Aquí está la fuente tipo sensor." |
| **Calidad de datos** | Meses con datos, el hueco de 2021, problemas encontrados y cómo se resolvieron | Franja roja = SIPSA no entregó datos (ene-2021 a ene-2022) | "Un dato sin su limitación declarada es peligroso." |
| **Clima y El Niño** | ONI (Pacífico vs lo normal) y lluvia por zona (NASA) | Arriba de +0,5 °C = El Niño; debajo de −0,5 = La Niña. Anomalía, no valor absoluto | "El clima mueve la oferta y se nota en el precio meses después." |
| **Producción y comercio** | Dependencia de importaciones por producto (FAOSTAT) | Barra larga = más del consumo viene de afuera → más expuesto al dólar | "FAO es anual: no sirve para alertar, sino para dar contexto." |

**Los dos términos que más preguntan:** *anomalía* = cuánto se aleja un valor de lo normal **de esa misma zona y mes**. *Dependencia de importaciones* = importaciones ÷ (producción + importaciones − exportaciones).

## 5. Las diapositivas, una por una (cifras verificadas)
| # | Tema | Qué decir | Quién (según las notas) |
|---|---|---|---|
| 1 | Portada | "¿Qué alimento se está disparando?" Sistema de alerta temprana con 6 fuentes y 20 mercados | Integrante 1, 0:00 |
| 2 | El problema | Volatilidad **135 %** del limón Tahití; una serie en Bogotá va de **698 a 6.075** COP/kg (casi ×9) | Integrante 1 |
| 3 | 5 porqués e Ishikawa | Léanlo de abajo hacia arriba con "por eso": termina en *falta un sistema que adquiera, homologue e integre* | Integrante 1 |
| 4 | Objetivo SMART | 33 alimentos · 20 mercados · 504 series · |z| > 2 y > 3 · fuentes abiertas, Python + DuckDB · prototipo 30-sep | Integrante 1 |
| 5 | Seis fuentes, tres tipos | **Sensor:** IDEAM. **API:** SIPSA (SOAP), NASA POWER (REST). **Archivo:** FAOSTAT, ONI, Pink Sheet | Integrante 2, 1:30 |
| 6 | Digitalización del sensor | Muestreo **10 min** · resolución **0,1 mm** · **11 bits** (0–200 mm ÷ 0,1 mm = 2.000 niveles; 2¹¹ = 2.048 alcanza, 2¹⁰ = 1.024 no) | Integrante 2 |
| 7 | Pipeline ETL | Extraer → transformar → homologar → cargar → detectar | Integrante 3, 3:15 |
| 8 | Integración | Una fila une 4 fuentes. Papa Bogotá jul-2026: 1.809,6 COP/kg · lluvia 47,4 mm (Boyacá) y 43,0 mm (Cundinamarca) · relación uno a muchos | Integrante 3 |
| 9 | Demo de la app | 504 series · **0 rojas y 7 amarillas** en agosto de 2026 | Integrante 3 |
| 10 | Conclusiones | Homologar no es uno a uno (13 de 33 comparan con FAO) · el hueco se declara · falta validar las alertas | Integrante 3, hasta 5:00 |

**Los diagramas:**
- **5 porqués:** problema = el precio de perecederos se dispara y nadie avisa → oferta cae brusco → perecederos no se almacenan → las señales previas no se vigilan junto al precio → están en fuentes distintas → no existe un sistema que las integre. **Causa raíz = falta un sistema de adquisición e integración con alerta.**
- **Ishikawa:** 6 ramas de causas (clima, producción, costos/insumos, mercado/logística, datos e información, institucional) que desembocan en el problema; las consecuencias van aparte (el productor no planea, el consumidor paga más, decisiones públicas tardías, pérdida de alimentos). Cada causa puede ser una pregunta.
- **Pipeline:** 6 fuentes → extraer → transformar → homologar → cargar → detectar → app.
- **DAQ:** lluvia (mm) → pluviómetro de balancín → muestreo cada 10 min → cuantificación (pulsos × 0,1 mm) → codificación (binario / JSON) → dato digital.

## 6. Mini-glosario
- **API:** dirección web a la que un programa le pide datos y recibe respuesta ordenada. **SOAP / REST / Socrata:** tres "idiomas" de API (SOAP es el viejo, en XML; REST y Socrata devuelven JSON).
- **ETL:** Extraer, Transformar, Cargar. **Pipeline:** esa secuencia automatizada.
- **Homologar:** hacer que nombres distintos de lo mismo se reconozcan. **Tabla puente:** la tabla que traduce entre dos vocabularios.
- **Modelo estrella:** tablas de *hechos* (precios, clima) al centro y de *dimensiones* (tiempo, mercado, producto) alrededor.
- **Join interno / externo izquierdo:** el interno deja solo lo que coincide; el externo izquierdo conserva todo lo de la izquierda aunque no coincida.
- **DuckDB:** base de datos en un solo archivo. **Streamlit:** librería de Python para hacer la app.
- **ONI:** índice de cuánto más caliente/frío está el Pacífico. **ENSO:** El Niño–La Niña.
- **DAQ:** adquisición de datos: magnitud física → sensor → **muestreo** (cada cuánto), **cuantificación** (a qué nivel), **codificación** (en binario). **Nyquist:** muestrear al menos al doble de la rapidez del fenómeno.

## 7. Preguntas difíciles y respuestas honestas
- **¿Predicen precios?** No: **detectan** movimientos anormales. Predecir sería otro proyecto.
- **¿Las alertas sirven de verdad?** Aún **no están validadas** contra crisis reales; es lo que falta.
- **¿Los umbrales 2 y 3 son un estándar?** No, los fijamos nosotros y se pueden cambiar.
- **¿El sensor es el del IDEAM?** El **dato** sí es real (dataset, columnas y sensores 0240/0257 verificados). Los pasos de la cadena DAQ usan un pluviómetro de balancín **como referencia de diseño**; el rango de 0–200 mm es un **supuesto de diseño**, y no es el modelo confirmado del IDEAM.
- **¿Por qué solo lluvia del IDEAM?** La temperatura (`sbwg-7ju4`) está verificada pero no se descargó.
- **¿Por qué SIPSA alerta y FAOSTAT no?** SIPSA es diaria; FAO es anual con un año de rezago.
- **¿Se puede calcular el margen de intermediación?** No: SIPSA y FAO para precios vienen del mismo sistema del DANE y no son independientes.
- **¿Qué hicieron con los faltantes?** Se declaran, no se rellenan. El hueco de 2021 corta el cálculo del retorno.
- **¿Por qué anomalías de clima?** NASA POWER promedia una cuadrícula de ~50 km que mezcla valle y montaña (a Villavicencio, a 467 m, le asigna 1.392 m); la anomalía compara la zona consigo misma y el error se cancela.
- **¿Por qué hay más filas al unir con las zonas?** La papa tiene dos zonas productoras.

## 8. Para cuidar hoy
- Las diapositivas dicen **"Equipo X"** y **"[Nombre 1] [Nombre 2] [Nombre 3]"**: cámbienlos.
- La portada de la app usa el **último mes cerrado (agosto)**: 0 rojas y 7 amarillas, igual que la diapositiva 9. Septiembre está abierto y puede mostrar otras cifras (hoy: 2 rojas y 9 amarillas); la app avisa que el mes no ha terminado.
- Tengan la app **corriendo antes** de empezar: `.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py`. Y capturas de pantalla de respaldo por si falla el computador.
- Los tiempos son **5 min + 2 de preguntas**: ensayen con cronómetro.
