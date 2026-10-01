# Guion de presentación — Caso 8

Diez minutos, alineado con el deck real (`entrega_AE2/.../Anexo3_AE2_EquipoX_30092026.pptx`, 10
diapositivas). Las frases entre comillas son para decirlas en voz alta: cortas, sin leer la
diapositiva. Todas las cifras salen de la base `data/processed/caso8.duckdb` (último mes cerrado:
**agosto de 2026**; septiembre es parcial).

**Índice**

1. [Mapa de tiempos](#mapa-de-tiempos)
2. [Diapositiva por diapositiva (1 a 10)](#diapositiva-por-diapositiva)
3. [Recorrido de la demo en vivo (diapositiva 9)](#recorrido-de-la-demo-diapositiva-9-3-minutos)
4. [Cómo explicar cada gráfica](#cómo-explicar-cada-gráfica)
5. [Plan B si la app no abre](#plan-b-si-la-app-no-abre)
6. [Preguntas que te van a hacer](#preguntas-que-te-van-a-hacer)

Antes de empezar: abrí la app 5 minutos antes, en la página **Inicio**, y dejá otra pestaña lista
con el comando del Plan B. Cerrá `integrar.py` y cualquier otro proceso que tenga la base abierta.

---

## Mapa de tiempos

| # | Diapositiva | Tiempo | Qué mostrás |
|--:|---|---:|---|
| 1 | Portada | 0:15 | La diapositiva |
| 2 | El problema | 1:00 | 135 % y ×9 |
| 3 | Causa raíz (5 porqués + Ishikawa) | 1:00 | La imagen |
| 4 | Objetivo SMART | 0:30 | Las cinco letras |
| 5 | Adquisición: seis fuentes, tres tipos | 1:00 | Las tres columnas |
| 6 | Digitalización del sensor | 0:45 | 10 min, 0,1 mm, 11 bits |
| 7 | Pipeline ETL | 0:45 | La imagen |
| 8 | Integración: una fila, cuatro fuentes | 0:45 | La tabla de ejemplo |
| 9 | Demo de la app | 3:00 | La app en vivo |
| 10 | Conclusiones | 0:50 | Las tres tarjetas |
| | **Total** | **9:50** | 10 s de margen |

---

## Diapositiva por diapositiva

### 1 · Portada — 0:15

> "Buenas. Somos el equipo X. Respondemos una pregunta: ¿qué alimento se está disparando?
> Integramos seis fuentes de datos para avisar cuando un precio mayorista se mueve de forma
> anormal en 20 mercados de Colombia."

**Mostrar:** nada más; decí los nombres del equipo.

### 2 · El problema — 1:00

Abrí con el dato, no con la definición.

> "El limón Tahití tiene una volatilidad anualizada mediana del 135 %."
> "Una sola serie en Bogotá va de 698 a 6 075 pesos el kilo. Casi nueve veces. El pico y el valle
> están separados por tres meses."
> "El productor no puede planear la siembra. El consumidor ve saltar la canasta."
> "Los datos para anticiparlo existen, son seis fuentes, pero están dispersas. Nadie las junta."

Verificado: la mediana de volatilidad del limón Tahití es 135,4 %. En Bogotá el máximo fue 6 074,83
(marzo 2023) y el mínimo 698,09 (junio 2023, tres meses después): 8,7 veces, que la diapositiva redondea a ×9.

**Mostrar:** la diapositiva (135 %, ×9, 6 fuentes).

### 3 · Causa raíz: 5 porqués e Ishikawa — 1:00

> "Preguntamos cinco veces por qué. Los precios saltan porque la oferta cambia de golpe. Nadie
> lo ve venir porque la información llega tarde y separada."
> "El Ishikawa agrupa las causas. La que podemos atacar con datos: la información existe pero no
> está integrada."
> "No atacamos la sequía ni el transporte. Atacamos el aviso tardío."

**Mostrar:** la imagen; seguí con el dedo el camino de los porqués hasta la causa raíz.
Cerrá con el puente: "Esa causa raíz define el objetivo."

### 4 · Objetivo SMART — 0:30

> "S: 33 alimentos en 20 mercados. M: 504 series vigiladas, con alerta amarilla sobre 2
> desviaciones y roja sobre 3. A: fuentes abiertas, Python y DuckDB. R: sirve al productor, a la
> central mayorista y al Estado. T: prototipo el 30 de septiembre, alerta mensual."

Si preguntan por 504 y no 660 (33 × 20): no todo mercado vende todo producto. En agosto de 2026
hay 504 series con dato; en toda la historia hay 559 combinaciones mercado-producto.

### 5 · Adquisición: seis fuentes, tres tipos — 1:00

> "Seis fuentes, de tres tipos. Un sensor: el IDEAM, lluvia cada diez minutos. Dos APIs: SIPSA,
> con el precio mayorista diario, y NASA POWER, con el clima por zona. Y tres archivos: FAOSTAT,
> ONI y Pink Sheet."
> "La alerta nace en SIPSA porque publica a diario. FAOSTAT sale una vez al año con un año de
> retraso: aporta contexto, no señal."

**Historia 1 — la documentación mentía** (30 s, va aquí porque es la API de SIPSA):

> "La guía del DANE declara un endpoint HTTP. No procesa SOAP: responde una página HTML a todo.
> Por HTTPS sí funciona, y es SOAP 1.2, no 1.1. Eso no está escrito en ningún lado. Lo
> descubrimos probando antes de escribir código."

**Mostrar:** las tres columnas de la diapositiva (sensor, API, archivo).

### 6 · Digitalización del sensor — 0:45

> "¿Cómo se vuelve dato una gota de lluvia? Un pluviómetro de balancín: cada 0,1 milímetro vuelca
> una cubeta y genera un pulso. Se cuentan los pulsos."
> "El rango es de 0 a 200 milímetros con paso de 0,1: 2 000 niveles. Con 10 bits caben 1 024: no
> alcanza. Con 11 caben 2 048: alcanza. Por eso 11 bits."
> "Se registra cada 10 minutos y el IDEAM lo publica por API en datos.gov.co."

Decilo con honestidad: los pasos de transductor y bits son un **modelo de referencia** (por
ejemplo el TE525MM, de 0,1 mm por vuelco), no el equipo confirmado del IDEAM. Lo verificado contra
la fuente real es el dataset, sus columnas, los códigos de sensor 0240 y 0257 y sus frecuencias.

**Mostrar:** la diapositiva (10 min, 0,1 mm, 11 bits). Si hay tiempo, la página **Sensor IDEAM**
tiene la cadena completa.

### 7 · Pipeline ETL — 0:45

> "Cinco pasos: traer, limpiar, homologar, unir, detectar. Python hace la mayor parte, OpenRefine
> homologa los nombres de producto, y todo termina en una base DuckDB."
> "Los datos crudos no se tocan: quedan guardados con su fecha."

**Historia 2 — el número grande mentía** (25 s, va aquí porque es limpieza):

> "El chequeo de comercio arrojó 2 730 inconsistencias. Abrimos la primera: era `Fruit`, con
> producción cero. No es un cultivo, es un agregado. Filtrando bien quedaron 97, y solo 9 eran
> reales. De 2 730 a 9: la diferencia fue abrir el dato en vez de confiar en el agregado."

**Mostrar:** la imagen del pipeline, en orden.

### 8 · Integración: una fila, cuatro fuentes — 0:45

> "Esta es la fila que lo integra todo. El precio viene de SIPSA: papa negra en Bogotá, julio de
> 2026, 1 810 pesos. El departamento viene de la tabla puente. La lluvia, del IDEAM. La fase, de
> la NOAA: El Niño."
> "Las llaves son producto, departamento y año-mes."
> "La papa sale dos veces porque tiene dos zonas productoras, Boyacá y Cundinamarca. Es una
> relación de uno a muchos."

**Historia 3 — el código correcto mentía** (20 s):

> "Este cruce al principio unía cero filas de unas 34 mil. Corría sin un solo error. La
> configuración decía 'Papa' y SIPSA dice 'Papa negra'. Un join que no encuentra nada no se
> queja. Es el error más peligroso: el que no falla."

Si sobra tiempo: de 33 productos de SIPSA, solo 13 tienen correspondencia exacta con FAOSTAT (10
agregada, 8 genérica, 2 sin equivalente). Guayaba y mango tommy comparten el ítem 571 de FAO.

**Mostrar:** la tabla de la diapositiva. Señalá las dos filas de la papa.

### 9 · Demo de la app — 3:00

Ver [el recorrido de la demo](#recorrido-de-la-demo-diapositiva-9-3-minutos). Resultado a decir al
inicio:

> "504 series vigiladas. En agosto de 2026: cero alertas rojas y siete amarillas."

### 10 · Conclusiones — 0:50

> "Tres cosas. Uno: homologar no es uno a uno. Solo 13 de 33 productos comparan precio con FAO,
> y la app avisa cuando la comparación no es válida."
> "Dos: un hueco se declara. SIPSA no tiene datos de enero de 2021 a enero de 2022 y no lo
> rellenamos: se muestra."
> "Tres: falta validar. Las alertas detectan movimientos estadísticamente raros; no está
> comprobado que anticipen crisis de abastecimiento."
> "El entregable no es el dashboard. Es saber qué se puede y qué no se puede concluir con estos
> datos, y haberlo dejado escrito en el código, en la base y en la pantalla."

Si preguntan por qué más falta: la API de FAOSTAT exige token y quedó sin verificar (la carga
histórica sale de descargas masivas), y las zonas productoras son capitales departamentales, no
polígonos de cultivo.

**Mostrar:** las tres tarjetas y el enlace al repositorio.

---

## Recorrido de la demo (diapositiva 9, 3 minutos)

Orden pensado para contar una historia: qué pasa hoy, dónde, cuándo, por qué, y de dónde sale el
dato. Si vas corto, saltá los pasos 3 y 6.

| Min | Página | Qué hacés | Qué señalás |
|---|---|---|---|
| 0:00 | **Inicio** | Ya está abierta | Los cuatro contadores: 504 series, 0 rojas, 7 amarillas, ONI +1,80 °C. Chip "Último mes cerrado: agosto 2026" y "septiembre en curso: datos parciales" |
| 0:30 | Inicio | Pasá el mouse sobre Bucaramanga en el mapa | Tarjeta superior: Chócolo mazorca en Bucaramanga, ▲ +41 %, z = +2,4. Los puntos grandes son mercados con alerta |
| 0:50 | **Semáforo de alertas** | Mes por defecto (agosto) | Lista ordenada de la más rara a la menos rara; mapa del mismo mes a la derecha. Decí que los umbrales son convenciones nuestras |
| 1:20 | Semáforo | Bajá al ranking | Limón Tahití y mango tommy arriba (135 % de volatilidad); coco y banano abajo (24-25 %) |
| 1:40 | **Detalle por producto** | Producto: Papa negra\*; mercado: BOGOTÁ, D.C. (vienen por defecto) | Banda min-max, la tarjeta "+171 % frente a hace un año" y que **no hay alerta**. Esa es la lección: ver "Cómo explicar" |
| 2:15 | **Sensor IDEAM** | Bajá al JSON crudo y a la lluvia mensual (Tolima) | Dato crudo → fila agregada: Tolima, julio 2026, 14,15 mm, 26 estaciones. "Esto conecta con la diapositiva 6" |
| 2:40 | **Calidad de datos** | Barras de series por mes | La franja roja del hueco 2021. "Un hueco se declara" |
| 2:55 | Cierre | Volvé a Inicio o a la diapositiva 10 | "Todo esto se recalcula solo cuando entran datos nuevos" |

Páginas que **no** abrís en la demo, pero sabés explicar: Lo que va de 2026, Recorrido paso a paso,
Clima y El Niño, Producción y comercio. Si el jurado pregunta por ellas, ver abajo.

Aviso útil: si cambiás el mes a septiembre en el Semáforo vas a ver 2 rojas y 9 amarillas. Es un
mes abierto con pocos días; la app lo advierte. No lo uses en la demo.

---

## Cómo explicar cada gráfica

Formato: **qué muestra**, **cómo se lee**, **lo que decís**. Los ejemplos salen de la base
(`alertas()` de `src/indicators/volatilidad.py` sobre `fact_precio_mayorista`).

### Inicio

**Contadores.** Cuatro números del último mes cerrado: series vigiladas, alertas rojas, amarillas
y el índice ONI. Se lee de izquierda a derecha, de lo general a lo urgente.
> "Vigilamos 504 series. En agosto ninguna roja y siete amarillas. Y el Pacífico está 1,80 grados
> más caliente de lo normal: hay El Niño."

**Tarjetas de alertas.** Una por alerta, ordenada por rareza. Flecha ▲/▼ es el cambio frente al mes
anterior; "z" son las desviaciones.
> "La más rara de agosto: el chócolo en Bucaramanga subió 41 % en un mes, a 1 996 pesos el kilo. Eso
> está 2,4 desviaciones fuera de lo normal para ese chócolo en ese mercado."

**Mapa de mercados con nombres.** Un punto por mercado. Color = la alerta más grave del mes;
tamaño = cuántos productos con alerta; gris-verde chico = sin alertas.
> "Cada ciudad es un mercado mayorista. Los puntos grandes son donde hay algo raro. En agosto hay
> siete mercados con una alerta cada uno: Armenia, Bucaramanga, Cali, Cartagena, Neiva, Pasto y
> Popayán. El mouse dice cuál."

### Lo que va de 2026

**Barras de variación interanual.** Cada barra es un producto; largo = cambio de su precio
(mediana nacional) de agosto 2026 frente a agosto 2025. Rojo = más caro, azul = más barato.
> "21 de 33 productos están más caros que hace un año; la mediana sube 13,8 %. La arracacha
> subió 188 % y la papa negra 156 %. La remolacha y la zanahoria bajaron 56 y 55 %."

**Alertas por mes.** Columnas apiladas: amarillo = amarillas, rojo = rojas.
> "En 2026 hay 94 alertas hasta agosto. El pico fue marzo, con 29: 25 amarillas y 4 rojas. Agosto
> fue tranquilo: 7."

**ONI.** Un punto por trimestre móvil; rojo sobre +0,5 °C (El Niño), azul bajo −0,5 °C (La Niña),
gris normal.
> "Empezamos el año en La Niña débil, con −0,60 en el trimestre noviembre-enero. En abril-junio
> cruzó +0,5 y hoy está en +1,80. Pasamos de La Niña a un El Niño fuerte en menos de un año."
> (El valor más reciente, JJA 2026, es provisional.)

### Semáforo de alertas

**Lista de alertas.** Una fila por alerta, ordenada de la más rara a la menos rara. "Cambio del
mes" es lo que subió o bajó; z-score a cuántas desviaciones quedó.
> "Agosto: siete amarillas. Cuatro son chócolo (Bucaramanga, Popayán, Pasto, Neiva), una piña en
> Cali, una ahuyama en Cartagena que bajó 37 %, y una granadilla en Armenia que bajó 24 %."

**Mapa del mes.** Mismos colores y tamaños que el de Inicio, para el mes elegido.
> "Las alertas no están concentradas en una región: son siete puntos sueltos. Eso nos dice que
> agosto no fue una crisis general, fueron movimientos locales."

**Ranking de volatilidad.** Barras horizontales: volatilidad anualizada mediana por producto.
Más larga = sube y baja más.
> "Limón Tahití y mango tommy, 135 %. En el otro extremo, coco 24 % y banano 25 %. Ojo: un
> producto muy volátil casi no dispara alertas, porque para él los saltos grandes son lo normal.
> El limón tiene 17 alertas amarillas y ninguna roja; el coco, con la menor volatilidad, tiene 14
> rojas."

### Detalle por producto (Papa negra\* en BOGOTÁ, D.C.)

**Gráfica de precio con banda.** Línea verde = precio promedio de cada mes (eje vertical, pesos por
kilo). Banda clara = del precio más bajo al más alto del mes. Círculo amarillo/rojo = mes con alerta.
Donde la línea se corta no hay datos.
> "Papa negra en Bogotá, 67 meses con dato. Agosto de 2026: promedio de 2 261 pesos, con rango entre
> 1 875 y 2 625 según el día. Hace un año valía 834: subió 171 %."
> "Pero fijate: en 2026 no hay un solo círculo. La alerta mira el cambio de un mes a otro, no si el
> precio está caro. La papa subió escalonada, no de golpe."
> "La línea se corta de enero de 2021 a enero de 2022: ese es el hueco de SIPSA, no lo rellenamos."

**Barras de z-score con franjas.** Cada barra es un mes. Franja blanca (entre −2 y +2) = normal;
amarilla (2 a 3) y roja (más de 3) = raro. Las barras toman el color de su alerta.
> "Noviembre de 2025 es el salto más grande reciente: la papa subió 38 % en un mes, de 809 a 1 117.
> La barra llega a 1,8: casi toca la franja amarilla, pero no. Es lo normal para esta serie, que
> es muy movida. La única alerta de esta serie es mayo de 2022, amarilla, con z = −2,3."
> "Otro ejemplo para contrastar: el limón Tahití en Bogotá pasó de 2 629 a 6 075 pesos entre enero y
> marzo de 2023 sin encender ninguna alerta (z = 0,9). Volátil por naturaleza."

**Recuadro de FAO.** Un mensaje verde, amarillo o rojo según se pueda comparar con el precio al
productor.
> "Para la papa negra la app dice 'solo en parte': FAO la mete en el ítem 116, Potatoes, junto con
> la papa criolla. Esa mezcla no sirve para comparar. La limitación viaja con el dato."

### Recorrido paso a paso

**De 20 precios diarios a 1 mensual** (papa negra, Bogotá, agosto de 2026). Puntos verdes = precio
de cada día; línea roja punteada = promedio del mes.
> "Veinte precios diarios se vuelven una sola fila: 2 261 pesos, mínimo 1 875, máximo 2 625, y
> `dias_con_dato` = 20. Ese último campo importa: un mes con dos días no vale lo mismo que uno con
> veinte."

Además: la tabla de problemas reales (mercado renombrado Cúcuta, `-999` de NASA, asterisco de
variedad) y la consulta SQL que une precio, clima y ONI. Sirve para responder "¿cómo integraron?".

### Sensor IDEAM

**Cadena de adquisición.** Ocho tarjetas: fenómeno, transductor, conteo, digitalización, registro,
transmisión, publicación, pipeline.
> "Es la diapositiva 6 con más detalle: lluvia, balancín, pulsos, 11 bits, registro a 10 minutos,
> GPRS, API Socrata, y nuestra consulta que suma por estación y mes."
Los pasos 2 a 4 son referencia de diseño; la página lo dice.

**Mapa de 450 estaciones.** Punto = estación, color = departamento; cuadrado oscuro = mercado
mayorista.
> "Medimos la lluvia en 450 estaciones de ocho departamentos productores: Antioquia 95, Boyacá 92,
> Cundinamarca 89, Tolima 55, Huila 46, Norte de Santander 36, Meta 21, Quindío 16. Hay lluvia
> medida cerca de varios mercados, pero no de todos: la costa no tiene estaciones nuestras."

**JSON crudo y agregado.** A la izquierda, dos lecturas reales de la API; a la derecha, la suma
mensual por estación; abajo, la fila ya agregada.
> "Una lectura cruda es esto: estación, sensor, minuto, milímetros. Nunca bajamos los millones de
> lecturas: pedimos que el servidor sume por estación y mes, y nosotros resumimos por departamento.
> Ejemplo: Tolima, julio de 2026, 14,15 milímetros, mediana de 26 estaciones, 50 por debajo de lo
> normal."

**Lluvia mensual por departamento.** Barras: azul = llovió más que el promedio de ese mes; café =
llovió menos. Eje en milímetros contra lo normal.
> "En julio de 2026 el Tolima, Huila y Meta estuvieron más secos de lo normal, mientras Antioquia
> recibió 63 milímetros de más. Los meses con pocas estaciones son menos confiables: agosto de
> Meta tiene una sola."

### Calidad de datos

**Barras de series por mes.** Altura = cuántas series (producto-mercado) tienen precio ese mes. La
franja roja marca el hueco.
> "Cada barra son unas 500 series. Entre enero de 2021 y enero de 2022 no hay ninguna: 13 meses
> sin datos. El servicio web del DANE no los entrega. No inventamos esos meses, y tampoco calculamos
> el cambio entre diciembre de 2020 y febrero de 2022, porque parecería un solo mes y daría alertas
> falsas."

**Tarjetas de hallazgos y tabla de ítems FAO que mezclan productos.** La tabla lista los seis
ítems de FAO que reciben más de un producto de SIPSA.
> "Esto es lo que encontramos revisando: Cúcuta renombrado, comercio de 2 730 a 9, la unidad de
> SIPSA confirmada contra FAO. Y esta tabla: el ítem 603 recibe granadilla, lulo, maracuyá y
> tomate de árbol. Su precio es una mezcla."

### Clima y El Niño

**Serie ONI desde un año elegido (por defecto 2000).** Área roja sobre cero (más caliente), azul
bajo cero (más frío), líneas punteadas en ±0,5 °C.
> "Si el índice pasa de 0,5 durante varios trimestres, se declara El Niño. Desde el año 2000 el pico
> fue el de 2015 con +2,59. Hoy estamos en +1,80 y subiendo."

**Lluvia NASA POWER por cultivo y zona.** Barras azul/café contra lo normal, en milímetros por
día, desde 2015. Ejemplo: papa en Boyacá.
> "NASA promedia una cuadrícula de 50 km que mezcla valle y montaña. Por eso no miramos la lluvia
> absoluta sino la anomalía, y el error de altura se cancela."

### Producción y comercio

**Barras de dependencia de importaciones.** Largo = parte del consumo que viene de afuera (100 % =
todo importado). Selector de año.
> "En 2024, garbanzo 99,97 %, trigo 99,76 %, lenteja 99,5 %, cebada 97,2 %. Son productos cuyo
> precio sube con el dólar. FAO publica con un año de retraso: sirve de contexto, no para alertar."

---

## Plan B si la app no abre

1. **Antes de empezar:** tené una captura de pantalla de la app en la diapositiva 9 (Inicio con los
   contadores y el mapa) y otra del detalle de papa negra. Si la app falla, decís lo mismo sobre la
   captura.
2. **Levantarla a mano** (desde la raíz del proyecto, Windows):

   ```
   .venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
   ```

   Abre en `http://localhost:8501`. Tarda unos segundos en cargar la primera vez.
3. **Si dice "No existe caso8.duckdb":** la base falta. Correr `.venv\Scripts\python.exe scripts\integrar.py`
   (tarda un rato; no lo hagas en vivo).
4. **Si la base está bloqueada o no escribe:** hay otro proceso con la base abierta. Cerrá la app
   anterior o `integrar.py` y volvé a lanzar.
5. **Si el puerto está ocupado:** agregá `--server.port 8502`.
6. **Última opción:** decí "la app corre en local, les muestro la captura" y seguí con la
   diapositiva 10. No pierdas más de 20 segundos peleando con el comando.

---

## Preguntas que te van a hacer

**¿Por qué no usaron la API de FAOSTAT?**
Exige token y no lo conseguimos a tiempo. La carga histórica sale de las descargas masivas, que
no piden credenciales, así que no bloquea nada. El módulo está escrito y marcado con lo que falta
verificar.

**¿Por qué DuckDB y no Postgres?**
Archivo único sin servidor, lee Parquet directo, y se versiona en el repositorio. La app lo lee
sin credenciales. Un servidor solo se justificaría si necesitáramos actualización automática en la
nube.

**¿Los umbrales de alerta de dónde salen?**
Son convenciones de este trabajo: 2 y 3 desviaciones estándar. No son estándares oficiales y está
dicho en la app y en el reporte. Calibrarlos requiere una lista de eventos conocidos.

**¿Por qué no calculan el margen entre precio mayorista y precio al productor?**
Porque las dos series no son independientes. Los 6 893 registros de precio al productor de
Colombia en FAOSTAT (en pesos por tonelada) llevan flag de cifra oficial, o sea que vienen del
gobierno colombiano, probablemente del mismo sistema del DANE que alimenta SIPSA. Restar una de
otra no mide intermediación.

**¿Por qué la lluvia de NASA y la del IDEAM no coinciden?**
NASA POWER es un producto modelado sobre una cuadrícula de unos 50 km; el IDEAM es la lectura de
un pluviómetro físico. Ejemplo de julio de 2026 en Boyacá: NASA da una anomalía de +2,6 mm/día y
el IDEAM, −31 mm en el mes frente a lo normal. Por eso usamos las dos como contexto y ninguna como
verdad única. Es una limitación declarada, no un error resuelto.

**¿Por qué 504 series y no 660?**
No todo mercado vende todo producto. En agosto de 2026 hay 504 combinaciones mercado-producto con
dato; en toda la historia aparecen 559.

**¿Las alertas anticipan crisis?**
No lo sabemos. Detectan movimientos estadísticamente anómalos, que es otra cosa. Validarlo
requiere contrastar contra eventos conocidos de abastecimiento, y es lo primero que haríamos con
más tiempo.

**¿Qué harían con más tiempo?**
Tres cosas, en este orden. Validar las alertas contra eventos conocidos de abastecimiento.
Refinar las zonas productoras con polígonos de UPRA en vez de capitales departamentales. Y sumar
los microdatos del DANE para extender la historia de precios y cubrir el hueco de 2021.
