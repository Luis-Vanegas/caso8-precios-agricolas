# Prompt: reorganizar el Caso 8 para que cualquiera lo entienda

Copia desde "CONTEXTO" hasta el final de la fase que quieras encargar. Cada fase es
independiente y termina en su propio Pull Request. Orden obligatorio: 1 → 2 → 3 → 4.

---

## CONTEXTO (va siempre, en todas las fases)

Trabajas en el repo `caso8-precios-agricolas`: un pipeline en Python que integra fuentes
públicas en DuckDB (`data/processed/caso8.duckdb`) y una app que avisa cuando un precio
mayorista de alimentos en Colombia se mueve de forma anormal y estima hacia dónde va.

Lee primero `CLAUDE.md` (comandos, reglas y trampas conocidas) y `docs/contrato_datos.md`.

**Quién lo va a usar.** Público general: una persona que compra o vende comida, no un
analista. Y un equipo de estudiantes con poca experiencia en Python que debe explicar
cada línea en una sustentación de 5 minutos. La vara para todo lo que entregues es
**entendible**: si una tabla, una columna, una gráfica o una función necesita que
alguien la explique en voz alta, todavía no está terminada.

**Reglas de trabajo.**
- Rama corta por fase desde `main` (`refactor/…`, `feat/…`, `docs/…`). Commits
  convencionales con descripción en español, sin atribución de IA. Pide permiso antes
  de `push` o de abrir el PR.
- Comentarios del código en español sin tildes; textos que ve el usuario, con tildes.
- Los datos crudos (`data/raw/`) no se tocan. Ningún hueco se rellena con datos inventados.
- Las pruebas corren sin red: `.venv\Scripts\python.exe -m pytest tests -q`.
- El informe del curso lo redacta el equipo. Entrega datos, tablas, código y
  explicaciones técnicas; los párrafos del informe los escriben ellos.
- Antes de decir "listo": corre pruebas e `integrar.py` (trae 29 chequeos) y reporta el
  resultado real, con los fallos si los hay.

**Fecha límite: 26 de noviembre de 2026.** Todo fusionado y probado el 24; el 25 es
solo para ensayar la presentación.

**Lo que exige el reto de la profesora** (PDF "Caso 8", curso Adquisición e Integración
de Datos). Esto es el piso; lo demás es mejora y nunca lo reemplaza:
- Los cinco dominios de FAOSTAT integrados: precios al productor, producción, comercio,
  **balances alimentarios** y **valor de la producción**. Ninguno se elimina.
- Python para adquirir; Python y **OpenRefine** para perfilar y limpiar; **Power Query**
  para integrar. En `TASKS.md` OpenRefine y Power Query siguen sin ejecutar: son
  obligatorios y hoy son el mayor riesgo de la entrega.
- Extracción automática de boletines, tratamiento de faltantes e inconsistencias.
- Respuesta a las 11 preguntas de "Estructura" (`docs/respuestas_estructura.md`).
- Reporte corto del proceso y presentación con fortalezas y debilidades.

**Lo que ya se midió en la base (15-nov-2026).** Parte de aquí; no lo vuelvas a auditar.

| Hallazgo | Evidencia |
|---|---|
| Hay 27 tablas; la app no usa 5 | `dim_zona_productora`, `fact_balance`, `fact_insumos`, `fact_tasa_cambio`, `fact_valor_produccion` no aparecen en `app/` |
| Sobran productos que no son de Colombia ni de la canasta | `dim_item_fao` tiene 497 ítems; solo 23 se enlazan con los 33 productos de SIPSA. `fact_comercio` trae 444 ítems (22 enlazados), `fact_produccion` 168 (23), `fact_balance` 122 (0 enlazados) |
| `fact_insumos` es todo el Pink Sheet | 71 materias primas mundiales (petróleo, té, madera…); solo los fertilizantes tienen relación con el caso |
| `dim_tiempo.primer_dia` es redundante | En las 802 filas el día es 1; se deriva de `periodo` |
| `dim_mercado.series` no se entiende | Es el número de productos con precio en ese mercado (`count(*)` en `src/integration/modelo.py`) |
| `elevacion_grilla_m` confunde | Es la altura que NASA POWER asigna a su celda de grilla, no la altura real de la zona; no entra en ningún cálculo |
| Dos tablas dicen lo mismo | `dim_producto_sipsa` y `puente_producto`: 33 filas, las mismas columnas. `dim_zona_productora` y `puente_zona_sipsa`: 9 filas cada una |
| "Artículo" y "producto" son dos niveles del mismo catálogo | 351 artículos (`art_id`, variedad y presentación) se agrupan en 136 productos en el precio semanal; el precio mensual usa 33 productos |
| `flag` es el código de FAO | A = oficial, E = estimado, I = imputado, X = cifra de organismo internacional. Ya existe la columna `imputado` derivada de él |
| El pronóstico no siempre sirve | De 43 series producto-mercado, el modelo le gana al pronóstico ingenuo ("el mes que viene será igual") en 14 |
| No existe ningún notebook | Los cálculos están en `src/indicators/` (5 archivos, ~850 líneas) |

---

## FASE 1 — Base de datos: de 27 tablas a máximo 14, con nombres que se explican solos

**Objetivo.** Que una persona abra la base y entienda qué hay sin leer documentación.

1. **Nombra por origen.** Cada tabla lleva un prefijo que dice de dónde viene el dato:
   - `col_` dato medido en Colombia (SIPSA-DANE, IDEAM).
   - `mundo_` dato de fuente internacional (FAO, NASA, NOAA, Banco Mundial, Open-Meteo).
   - `resultado_` lo que calcula este proyecto (alertas, quiebres, efecto del clima, pronóstico).
   - `catalogo_` listas de referencia (productos, mercados, calendario).

   El resto del nombre dice qué mide y cada cuánto: `col_precio_mayorista_mensual`,
   no `fact_precio_mayorista`.
2. **Deja solo lo relacionado con Colombia y la canasta, sin perder ningún dominio de
   FAOSTAT.** Las cinco tablas de FAO (`fact_produccion`, `fact_comercio`,
   `fact_balance`, `fact_valor_produccion`, `fact_precio_productor`) tienen las mismas
   columnas: únelas en una sola, `mundo_fao_colombia`, con una columna `dominio`. Así
   salen 4 tablas sin borrar nada de lo que pide el reto. Filtra sus ítems a los que
   corresponden a productos de la canasta. Los balances usan códigos agregados
   distintos ("Papas y productos"), por eso hoy ninguno enlaza: agrega esa
   equivalencia a `catalogo_producto`. Filtra `fact_insumos` a fertilizantes. Para
   `fact_tasa_cambio`, decide con evidencia: se usa en un cálculo o se elimina.
3. **Usa lo que hoy está guardado y nadie mira.** Balances y valor de la producción
   deben aparecer en al menos una vista de la app (disponibilidad de alimento por
   persona, dependencia de importaciones), porque el reto pregunta cómo influyen
   producción, comercio y disponibilidad en el precio al productor.
4. **Un solo catálogo de productos.** Une `dim_producto_sipsa`, `puente_producto` y
   `dim_item_fao` en `catalogo_producto`, con los niveles artículo → producto → grupo y
   el ítem FAO equivalente como columnas. Una fila por artículo. Haz lo mismo con las
   dos tablas de zonas productoras.
5. **Limpia las columnas.** Quita `primer_dia` y `elevacion_grilla_m`. Renombra
   `series` a `productos_con_precio`. Reemplaza `flag` por una columna legible
   (`calidad_dato`: oficial / estimado / imputado) y elimina la que quede duplicada.
   Revisa cada columna restante con la misma pregunta: ¿se usa?, ¿su nombre se entiende solo?
6. **Escribe `docs/diccionario_datos.md`**: una sección por tabla con qué contiene en
   una frase, origen (nacional o internacional y fuente), qué representa una fila, y
   cada columna con unidad y ejemplo real. Abre con un diagrama Mermaid de cómo se
   conectan las tablas y una tabla "antes → después" de los 27 nombres viejos.
7. Actualiza `src/integration/modelo.py`, `src/integration/verificacion.py`,
   `app/datos.py`, `docs/contrato_datos.md`, la guía de Power Query
   (`docs/guia_powerquery.md`, `powerquery/`) y las pruebas.

**Terminado cuando:** la base tiene 14 tablas o menos; cada tabla y cada columna
aparece en el diccionario; ningún nombre viejo queda en `src/`, `app/`, `tests/` ni
`docs/` (compruébalo con una búsqueda); `integrar.py` y `pytest` pasan; la app actual
abre sus 7 páginas sin error.

---

## FASE 2 — Notebook que muestra los cálculos paso a paso

**Objetivo.** Responder "¿dónde están los scripts que hacen los cálculos que reportamos?"
con un archivo que se abre en GitHub y se lee de arriba abajo.

Crea `notebooks/calculos_paso_a_paso.ipynb`. El notebook **importa** las funciones de
`src/indicators/` (una sola fuente de verdad: el código vive en `src/`, el notebook lo
muestra funcionando). Lee la base en modo solo lectura.

Un capítulo por cálculo, en este orden: retorno mensual → volatilidad → z-score y
alertas → quiebres → efecto del clima con rezago → pronóstico y comparación con el
ingenuo. Cada capítulo sigue el mismo patrón:

1. **Para qué sirve**, en una frase sin fórmulas.
2. **La fórmula**, con cada símbolo nombrado.
3. **Un ejemplo a mano** con 5 o 6 filas reales de un producto conocido (papa o tomate
   en Bogotá), donde se vea el número entrar y salir.
4. **La función real** aplicada a esa serie, con el enlace a su archivo y línea.
5. **Una gráfica** del resultado.
6. **Cómo se lee** y qué limitación tiene (por ejemplo: SIPSA no tiene datos de
   2021-01 a 2022-01, por eso los retornos solo se calculan entre meses consecutivos).

Cierra con una tabla "cifra reportada → celda que la produce" para cada número que el
equipo usa en el informe y en las diapositivas (`docs/reporte.md`, `docs/guion_presentacion.md`).

**Terminado cuando:** el notebook corre completo de principio a fin sin red y sin
errores (`jupyter nbconvert --execute`); queda guardado con las salidas visibles; cada
función pública de `src/indicators/` aparece en algún capítulo; `README.md` enlaza el notebook.

---

## FASE 3 — App para el público: 3 módulos y un tablero de semáforos

**Decisión de Luis (marca una antes de encargar esta fase):**
- [ ] **A. Migrar a Next.js** (recomendada si quedan 7 días o más). Python exporta a
  `web/public/datos/*.json` con un script nuevo `scripts/exportar_web.py`; la web es
  estática, sin servidor, y se publica en Vercel. Control total del diseño y enlace
  público. Costo: el equipo no conoce TypeScript, así que la web se presenta como
  "la vitrina" y la sustentación técnica se apoya en el notebook de la Fase 2.
- [ ] **B. Quedarse en Streamlit** (si quedan menos de 7 días). El tablero de semáforos
  se arma como tabla HTML propia dentro de Streamlit. Menos riesgo, diseño más limitado.

En las dos opciones el contenido y la estructura son los mismos:

**Antes de diseñar**, mira cómo resuelven esto tres tableros públicos de precios de
alimentos (FAO Food Price Monitoring and Analysis, WFP DataViz/HungerMap, el boletín
de SIPSA del DANE) y anota en `DESIGN.md` qué patrón tomas de cada uno y por qué.

**Módulo 1 — "Precios hoy y lo que viene"** (la portada, y el centro del proyecto).
Una tabla estilo Power BI, una fila por producto, ordenada de lo más urgente a lo más tranquilo:

| Producto | Precio hoy ($/kg) | vs. mes pasado | vs. mismo mes del año pasado | Estado | Últimos 12 meses | Próximos 3 meses | Confianza |
|---|---|---|---|---|---|---|---|
| Tomate | 3.450 | ▲ +18 % | ▲ +32 % | 🔴 Subida fuerte | minigráfica | ▲ sube a ~3.700 | Alta |

- **La predicción y la comparación son lo primero que se ve**, sin abrir menús ni
  desplegables. Cada comparación lleva su propio color y flecha: rojo ▲ si subió más
  de lo normal, verde si está dentro de lo normal, azul ▼ si bajó más de lo normal.
  "Normal" es el rango histórico de ese producto en ese mismo mes, no un porcentaje fijo.
- **Ventana de tiempo por defecto: de hace 12 meses a 3 meses adelante.** Toda gráfica
  de serie abre así, con una línea vertical en "hoy": a la izquierda lo observado, a
  la derecha el pronóstico con su banda. El historial completo queda a un clic.
- **Estado** sale de la alerta por z-score que ya calcula `src/indicators/volatilidad.py`;
  usa sus umbrales, no inventes otros. Verde = movimiento normal, amarillo = atención,
  rojo = movimiento anormal.
- El color siempre va acompañado de flecha y palabra, para que se entienda sin ver colores.
- **Próximo mes** sale de `pronostico_precio`. **Confianza** dice la verdad: "Alta"
  solo donde el modelo le gana al ingenuo; en el resto muestra "Baja: mejor suponer
  que sigue igual". Un pronóstico poco confiable mostrado como seguro es peor que no mostrarlo.
- Filtro por mercado. Al tocar un producto se abre su detalle: serie histórica con la
  banda de rango normal, alertas marcadas y el pronóstico con su intervalo.
- Usa el último mes cerrado (`mes_cerrado`), nunca el mes abierto.

**Módulo 2 — "Dónde y por qué"**. Mapa de Colombia por departamento coloreado con el
mismo semáforo (unir por `dpto_codigo`, nunca por nombre). Al lado, el clima: lluvia
observada frente a lo normal, fase de El Niño/La Niña, y qué productos son sensibles a
la lluvia y con cuántos meses de rezago. Lenguaje de pista, no de causa: "cuando llueve
menos en Boyacá, la papa suele subir 2 meses después".

**Módulo 3 — "Los datos y cómo se hizo"**. Las fuentes en dos columnas claramente
separadas: **Nacionales** (SIPSA-DANE, IDEAM) e **Internacionales** (FAO, NASA, NOAA,
Banco Mundial), cada una con qué aporta, cada cuánto se actualiza y la fecha del
último dato. Debajo: el antes y después de cada fuente (filas crudas → filas limpias,
qué se corrigió), el diagrama de tablas del diccionario, los chequeos de calidad y la
descarga de tablas.

**Gráficas.** Solo tipos que cualquier persona ya conoce: líneas para el tiempo,
barras para comparar, mapa para el territorio, minigráficas en la tabla. Cada gráfica
lleva un título que dice la conclusión ("El tomate subió 18 % en octubre"), ejes con
unidad y una frase debajo de cómo leerla.

**Correcciones que pidió el equipo al revisar la app actual** (aplican en A y en B):
- La explicación de cada gráfica va visible debajo de ella, fuera de cualquier
  desplegable. Caso concreto: la gráfica de barras "frente al año anterior" compara
  el precio del último mes cerrado con el del mismo mes del año pasado, producto por
  producto; hoy esa frase está escondida.
- En la gráfica de lluvia y temperatura, la temperatura mínima y la máxima se
  confunden: usa dos colores claramente distintos (frío/cálido) y etiqueta cada línea.
- En la tabla de hallazgos del clima, la columna "Probabilidad de casualidad" se
  confunde con "causalidad". Renómbrala "Probabilidad de que sea azar" y deja la
  advertencia "correlación no es causalidad" en una frase aparte.
- Cada cifra calculada enlaza a su capítulo del notebook ("¿cómo se calculó?").

**Terminado cuando:** la app tiene exactamente 3 módulos; todo lo que hoy muestran las
7 páginas y 9 secciones quedó ubicado en uno de ellos o eliminado con justificación
escrita en el PR; una persona ajena al proyecto dice en 10 segundos qué productos
están en rojo y cuáles van a subir; se ve bien en celular (375 px) y en proyector;
contraste AA; capturas de los 3 módulos adjuntas en el PR.

---

## FASE 4 — Documentación y material para el equipo

1. `README.md` reescrito para alguien que llega de cero: qué es, qué responde, cómo
   correrlo en 3 comandos, mapa de carpetas ("¿dónde está cada cosa?") con enlace al
   notebook y al diccionario.
2. Cada carpeta de `src/` con un `LEEME.md` de 10 líneas: qué hace, qué recibe, qué entrega.
3. Revisa `docs/`: fusiona lo que se repite y borra lo que quedó viejo tras las fases 1 a 3.
4. `docs/insumos_informe.md`, **solo datos y tablas** para que el equipo redacte:
   - Antes y después de cada fuente (filas, columnas, nulos, duplicados, qué se corrigió),
     tomado de `docs/perfilado.md` y de `src/profiling/`.
   - Ficha del sensor IDEAM: qué mide, cada cuánto, cuántas estaciones, en qué cálculo
     se usó (a partir de `docs/sensor_ideam.md`).
   - Resultados de validación: los 29 chequeos y el desempeño del pronóstico frente al ingenuo.
   - Hechos medidos que sirven de materia prima para el Ishikawa, los 5 porqués, el
     objetivo SMART y las conclusiones. El equipo los redacta.
   - Lista de trabajos previos similares con referencia verificable (parte de
     `docs/fuentes_y_referencias.md`; no cites nada que no hayas abierto).

5. `docs/guia_del_proyecto.docx`: un Word de estudio para el equipo, generado desde el
   diccionario y el notebook para que no se desactualice. Contenido: qué problema
   resuelve, de dónde sale cada dato (nacional o internacional), cómo quedó la base
   (diagrama y tablas), cada cálculo explicado con su ejemplo, cómo leer cada pantalla
   de la app, fortalezas y debilidades medidas, y un glosario. Es material de estudio:
   el informe que se entrega lo redacta el equipo con sus palabras.
6. Deja lista la evidencia de OpenRefine y Power Query: guías actualizadas a los
   nombres nuevos de las tablas y una lista exacta de las capturas que el equipo debe tomar.

**Terminado cuando:** cada pendiente de la lista del equipo tiene un archivo o una
sección que lo cubre con datos; ningún documento describe tablas, páginas o comandos
que ya no existen; un integrante nuevo encuentra los cálculos, la base y la app
siguiendo solo el README.
