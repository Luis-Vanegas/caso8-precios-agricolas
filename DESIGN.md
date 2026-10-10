# DESIGN.md — Caso 8 · Precios agrícolas

Fuente de verdad visual de la app Streamlit. Cualquier página nueva (y cualquier agente que la
escriba) parte de aquí. Los valores viven en código en `app/estilo.py`; si este archivo y
`estilo.py` no coinciden, se corrige uno de los dos en el mismo commit.

## Overview

App académica que muestra cuándo el precio mayorista de un alimento se mueve de forma anormal y
qué tiene que ver el clima. La usan cinco estudiantes y un jurado, sobre todo **proyectada en un
auditorio durante una sustentación de 5 minutos**, y después alguien que la abre por curiosidad.
Tiene que sentirse seria y cercana a la vez: datos públicos colombianos, explicados sin jerga.

**Dirección:** Editorial de campo — papel cálido, títulos con serifa, números en monoespaciada,
color reservado para el significado (semáforo y fases del clima).

**Por qué:** baja frecuencia de uso y lectura a distancia piden aire, tipografía grande y pocas
señales fuertes; el tono editorial hace que una cifra se lea como un hallazgo, no como un log.

## Restricciones

- Marca: ninguna institucional. Identidad propia inspirada en el campo y la bandera de Colombia.
- Accesibilidad: WCAG AA mínimo (4,5:1 texto, 3:1 marcas gráficas). Proyector: cuerpo ≥ 15px en gráficas.
- Daltonismo: el semáforo **nunca** se comunica solo con color (verde y rojo se confunden con deuteranopía).
- Soporte: Streamlit 1.6x, solo tema claro (la app no define tema oscuro).
- Textos en pantalla con tildes; comentarios del código sin tildes (regla 5 de `CLAUDE.md`).
- No negociable: el semáforo rojo/amarillo/verde y los colores de El Niño (rojo) y La Niña (azul).

## Color

Lienzo y tinta (valores actuales de `estilo.py`; contraste medido el 2026-10-09):

| Token (`estilo.py`) | Valor | Contraste sobre `PAPEL` | Uso |
|---|---|---|---|
| `PAPEL` | `#FAF7F0` | — | Fondo de página |
| (superficie) | `#FFFFFF` | — | Tarjetas, fondo de gráficas |
| barra lateral | `#F1ECDF` | — | Menú |
| `TINTA` | `#1C2521` | 14,7:1 | Texto principal, títulos |
| `GRIS` | `#6B7065` | 4,75:1 | Texto de apoyo, notas. Mínimo permitido para texto |
| `BORDE` | `#E6E0D2` | 1,23:1 | Separadores, borde de tarjetas. Nunca texto |
| rejilla de gráfica | `#EFEAE0` | — | Líneas de fondo de Plotly |

No se usa una escalera alpha: la rampa cálida actual es coherente y reexpresarla no cambia nada
visible. No agregar grises nuevos; si hace falta un tercer nivel de texto, usar `GRIS`.

Acento (uno solo):

| Token | Valor | Uso permitido |
|---|---|---|
| `VERDE` | `#1B5E3B` | Antetítulo, etiqueta del recuadro "En palabras simples", número de paso. Además es "verde" del semáforo |

Semánticos (nunca se neutralizan ni se reutilizan para decorar):

| Token | Valor | Significado | Sobre `PAPEL` |
|---|---|---|---|
| `ROJO` | `#C0392B` | Alerta roja · El Niño · precio sube | 5,08:1 |
| `AMARILLO` | `#E9B824` | Alerta amarilla | **1,73:1** |
| `VERDE` | `#1B5E3B` | Sin alerta | 7,24:1 |
| `AZUL` | `#1D4E89` | La Niña · lluvia · precio baja | 7,84:1 |
| `TIERRA` | `#8A5A2B` | Serie secundaria · temperatura | 5,49:1 |

**Reglas de color de este producto:**
- `AMARILLO` es solo **relleno** (celda, punto, borde grueso ≥ 6px) con texto `TINTA` encima
  (8,49:1). Nunca como color de texto ni de línea fina: no se ve.
- Sobre `ROJO` y `VERDE` el texto va en blanco (5,44:1 y 7,75:1).
- Todo estado del semáforo lleva además un glifo o palabra: `▲` roja, `●` amarilla, `▼`/`—` verde,
  o la palabra ("roja", "amarilla") en la celda o el tooltip.
- `COLOR_ALERTA` es el único lugar que asigna color a un estado; las páginas lo importan, no
  escriben hex.
- La franja tricolor (amarillo 2 · azul 1 · rojo 1) es la marca de la app: va arriba de cada página y
  no se reinterpreta como dato.

### Escalas para las páginas nuevas

| Página | Codificación | Escala |
|---|---|---|
| Semáforo de la canasta | estado por celda (producto × periodo) | categórica `COLOR_ALERTA`; glifo solo en las celdas encendidas (`▲` roja, `●` amarilla) y estado en palabras en el tooltip de toda celda; celda sin dato en `#FFFFFF`, sin texto |
| Mapa | cambio % de precio por departamento | divergente `AZUL` → `#FFFFFF` → `ROJO`, centrada en 0 y simétrica; sin dato: `#E6E0D2` con trama o nota |
| Clima hoy | lluvia / temperatura | lluvia en `AZUL`, temperatura en `TIERRA`; pronóstico con línea punteada del mismo color |
| La cadena | lluvia → toneladas → precio | tres paneles apilados con el mismo eje X; lluvia `AZUL`, toneladas `TIERRA`, precio `TINTA` |
| ¿Cuánto afecta el clima? | un hallazgo por tarjeta (`cifra`) + tablas | sin escala de color: solo la tarjeta de El Niño lleva borde `ROJO`; los hallazgos se cuentan "N de M" para que se vea también lo que no apareció |
| Pronóstico | observado, pronóstico, banda, ingenuo | observado `TINTA`; pronóstico `AZUL`; banda `AZUL` al 15 % de opacidad del relleno; ingenuo `GRIS` punteado |

Un hueco de datos (p. ej. SIPSA 2021-01 a 2022-01) se ve como hueco: la línea se corta, nunca se une.
En la matriz del semáforo el hueco es una franja de celdas blancas y el pie de la gráfica dice de
qué hueco se trata. Por qué sin "s/d" en cada celda: son 33 productos × 13 meses, y rotular las 429
celdas tapa la matriz que la página existe para mostrar. El color nunca va solo igual: el estado en
palabras está en el tooltip de toda celda, y las encendidas llevan glifo.

## Tipografía

- Títulos: `Fraunces` (Google Fonts, opsz 9..144) — serifa editorial, da la voz.
- Cuerpo y controles: `Inter` (Google Fonts).
- Números (métricas, contadores, cifras de tarjeta): `JetBrains Mono` — los dígitos no bailan al animar.

Pesos cargados (los únicos que existen en la app; pedir otro cae al vecino en silencio):
Fraunces 500 y 700 · Inter 400, 500 y 600 · JetBrains Mono 500.

Escala:

| Rol | Tamaño | Peso | Familia |
|---|---|---|---|
| Título de página (`encabezado`) | 2,4rem | 700 | Fraunces |
| H2 / H3 | Streamlit por defecto | 500–700 | Fraunces |
| Antetítulo | .75rem, mayúsculas, tracking .12em | 600 | Inter |
| Subtítulo | 1,05rem, máx. 60rem de ancho | 400 | Inter, `GRIS` |
| Cuerpo / recuadro simple | 1rem, interlineado 1,5 | 400 | Inter |
| Dato de tarjeta | 1,35rem | 500 | JetBrains Mono |
| Contador | 34px | 500 | JetBrains Mono |
| Nota / caption | .85–.95rem | 400 | Inter, `GRIS` |
| Texto en gráficas | 15px (título 16px) | — | Inter / Fraunces |

## Espaciado y forma

- Ritmo: múltiplos de .4rem / 8px, como ya usa `estilo.py`.
- Ancho máximo del contenido: 1280px.
- Radios: 14px tarjetas y contadores, 12px recuadros, 10px tablas, 999px chips. No inventar otros.
- Sombra: una sola, `0 1px 2px rgba(0,0,0,.04)` en tarjetas. Ninguna más.
- Grillas de tarjetas con `fila_de_tarjetas` (se acomodan solas); una tarjeta dominante por fila
  cuando haya una cifra principal.

## Componentes (en `app/estilo.py`)

| Pieza | Para qué | Regla |
|---|---|---|
| `encabezado` | Franja + antetítulo + título + subtítulo | Primera llamada visible de cada página |
| `para_presentar` | Recuadro "Para presentar": guion de memoria de quien expone | Uno por página, justo debajo del `encabezado`. 2-3 líneas: qué muestra y "Si te preguntan…". Fondo `#F1ECDF` (el de la barra lateral) con borde izquierdo `TINTA`, para no confundirse con el recuadro verde |
| `explicacion` | Recuadro "En palabras simples" | Uno por sección como máximo; lenguaje sin jerga |
| `cifra` + `fila_de_tarjetas` | Número grande con su significado en palabras, en la misma tarjeta | Toda cifra de cabecera dice qué es: "+2,2 °C" → "el Pacífico está 2,2 °C más caliente de lo normal: hay El Niño". `color` solo si es un estado |
| `tarjeta` + `fila_de_tarjetas` | Cifra con título y nota | Con `color` solo si representa un estado del semáforo |
| `contadores` | Cifras grandes animadas | Solo donde la cifra se explica sola (hoy, la sección del sensor IDEAM); la portada usa `cifra` |
| `chips` | Etiquetas de fuente o herramienta | `parcial` solo para "dato incompleto" |
| `grafica` | Pintar Plotly con la plantilla `caso8` | Siempre; nunca `st.plotly_chart` directo |
| `pesos` | `$1.996` | Todo precio en pantalla pasa por aquí |
| `decimal` | `2,2` / `+2,2` | Todo decimal escrito en texto pasa por aquí (coma decimal) |
| aviso de tabla faltante (por crear con C2-06) | Página nueva cuya tabla aún no existe | `st.info` amable con qué falta y quién la entrega; nunca un traceback |

## Movimiento

- Entrada `subir`: .6s ease-out, desfases de 80ms (`anim-1` a `anim-4`). Solo bloques de cabecera y tarjetas.
- `latido`: punto de las alertas rojas activas. Nada más late.
- Contadores: 1,1s una vez al cargar.
- Nunca se animan gráficas, tablas, mapas ni la matriz del semáforo.
- `prefers-reduced-motion`: ya resuelto en `estilo.py` (todo visible y quieto). Toda animación nueva
  agrega su reset ahí.

## Guardarraíles

- No agregar colores fuera de la paleta ni hex sueltos en las páginas: importar de `estilo`.
- No usar `AMARILLO` como texto ni línea.
- No comunicar el semáforo solo con color.
- No agregar gradientes (la franja tricolor es la única y es de bordes duros).
- No usar emoji como iconos de interfaz; el menú usa iconos `:material/...:`.
- No agregar más texto en mayúsculas forzadas que el antetítulo y la etiqueta del recuadro simple.
- No agregar librerías de UI: Streamlit + Plotly alcanzan. Si hace falta una, se pide en `TASKS.md`.
- Correlación no es causalidad: toda página que cruce clima y precio lo dice en pantalla.
- Verificar cada página en el navegador (puerto 8502) antes de darla por terminada.
