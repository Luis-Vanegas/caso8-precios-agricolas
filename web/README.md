# web/ — el sitio público (Next.js)

La vitrina del proyecto, en tres módulos:

| Módulo | Ruta | Qué responde |
|---|---|---|
| **Precios** | `/` | Qué alimentos subieron, cuáles bajaron, si es normal y qué se espera |
| **Mapa y clima** | `/mapa` | Dónde está más cara la comida, dónde llovió más o menos, El Niño y el sensor |
| **Los datos** | `/datos` | De dónde sale cada número (fuentes nacionales e internacionales), cómo se hizo y qué falta |

Es un sitio **estático**: no consulta la base de datos. Lee archivos JSON que escribe Python.

```
base DuckDB  →  scripts/exportar_web.py  →  web/public/datos/*.json  →  este sitio
```

## Cómo correrlo

Desde la raíz del proyecto:

```
.venv\Scripts\python.exe scripts\exportar_web.py     # actualiza los datos del sitio
npm --prefix web install                              # solo la primera vez
npm --prefix web run dev                              # abre http://localhost:3000
```

## Cómo se publica (GitHub Pages)

`.github/workflows/web.yml` construye y publica el sitio cuando cambia `web/` en `main`.
Hay que activarlo **una sola vez** en GitHub: *Settings → Pages → Source: GitHub Actions*.
Queda en `https://luis-vanegas.github.io/caso8-precios-agricolas/`.

Como en Pages el sitio vive en una subcarpeta, la construcción recibe esa subcarpeta en la
variable `NEXT_PUBLIC_BASE_PATH`. En local va vacía y no hay que hacer nada.

## Dónde está cada cosa

| Archivo | Qué hace |
|---|---|
| `app/page.tsx` | Módulo Precios: título, tablero y "cómo leer esta tabla" |
| `app/mapa/page.tsx` | Módulo Mapa y clima |
| `app/datos/page.tsx` | Módulo Los datos |
| `app/layout.tsx` | Fuentes, franja tricolor y menú |
| `app/globals.css` | Colores, tipografías y estilos del tablero (vienen de `DESIGN.md`, en la raíz) |
| `app/clima.css` | Iconos, la cadena del clima y la tabla de lluvia esperada |
| `app/modulos.css` | Estilos del menú, el mapa, el clima, la página de datos y las animaciones |
| `componentes/Tablero.tsx` | La tabla de semáforos, los filtros y el detalle de cada producto |
| `componentes/Graficas.tsx` | Minigráfica de cada fila y gráfica del detalle (SVG, sin librerías) |
| `componentes/MapaAnimado.tsx` | El mapa plano, el reproductor de meses y el ranking |
| `componentes/Mapa3D.tsx` | La vista 3D del mapa (deck.gl); se descarga solo si alguien la pide |
| `componentes/CadenaClima.tsx` | «¿El clima mueve los precios?»: la cadena El Niño → lluvia → comida que llega → precio, con cuánto se sostiene cada paso, y las pistas del mes |
| `componentes/Clima.tsx` | El Niño, la lluvia esperada y cómo mide el sensor |
| `componentes/Navegacion.tsx` | El menú de los tres módulos |
| `componentes/Contador.tsx` | El número que cuenta hasta su valor |
| `lib/formato.ts` | Cómo se escriben pesos, porcentajes y fechas, y cómo se lee el semáforo |
| `lib/geo.ts` | Cómo se convierte longitud y latitud en dibujo, y un valor en color |
| `lib/tipos.ts` | La forma de cada JSON |
| `public/datos/*.json` | Los datos. **No se editan a mano**: los escribe `scripts/exportar_web.py` |

## Librerías

Dos fuera de Next.js y React. **lucide-react** trae los iconos (flechas, lluvia, termómetro): dibujados a mano se veían distintos en cada navegador. **deck.gl** hace la vista 3D del mapa. Dibujar un país
en 3D con WebGL a mano sería mucho código difícil de explicar. Todo lo demás (mapa plano,
gráficas, animaciones) está hecho con SVG y CSS, sin librerías.

## Reglas

- **Los cálculos no viven aquí.** El sitio solo muestra; todo número sale de `src/indicators/`
  a través del exportador. Si un dato se ve mal, el arreglo va en Python.
- El color nunca va solo: toda dirección lleva flecha y signo, todo estado lleva su palabra,
  y en el mapa "sin dato" lleva trama.
- Lo que falta se dice: los departamentos sin dato, los pronósticos poco confiables y las
  relaciones que no se sostienen aparecen en pantalla.
- Las animaciones son de entrada y ocurren una vez. Quien pide menos movimiento en su sistema
  ve todo quieto.
