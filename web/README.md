# web/ — el tablero público (Next.js)

La vitrina del proyecto: una tabla que dice qué alimentos subieron, cuáles bajaron, si el
movimiento es normal y qué se espera para los próximos meses.

Es un sitio **estático**: no consulta la base de datos. Lee archivos JSON que escribe Python.

```
base DuckDB  →  scripts/exportar_web.py  →  web/public/datos/tablero.json  →  esta web
```

## Cómo correrla

Desde la raíz del proyecto:

```
.venv\Scripts\python.exe scripts\exportar_web.py     # actualiza los datos de la web
npm --prefix web install                              # solo la primera vez
npm --prefix web run dev                              # abre http://localhost:3000
```

Para publicarla: `npm --prefix web run build` deja el sitio en `web/out/`.

## Dónde está cada cosa

| Archivo | Qué hace |
|---|---|
| `app/page.tsx` | La página: título, tablero y "cómo leer esta tabla" |
| `app/layout.tsx` | Fuentes y franja tricolor |
| `app/globals.css` | Todos los estilos. Colores y tipografías vienen de `DESIGN.md` (raíz) |
| `componentes/Tablero.tsx` | La tabla de semáforos, los filtros y el detalle de cada producto |
| `componentes/Graficas.tsx` | La minigráfica de cada fila y la gráfica del detalle (SVG, sin librerías) |
| `lib/formato.ts` | Cómo se escriben pesos, porcentajes y fechas, y cómo se lee el semáforo |
| `lib/tipos.ts` | La forma del JSON |
| `public/datos/tablero.json` | Los datos. **No se edita a mano**: lo escribe `scripts/exportar_web.py` |

## Reglas

- **Los cálculos no viven aquí.** La web solo muestra; todo número sale de `src/indicators/`
  a través del exportador. Si un dato se ve mal, el arreglo va en Python.
- El color nunca va solo: toda dirección lleva flecha y signo, y todo estado lleva su palabra.
- Un pronóstico con confianza baja se muestra como tal. No se esconde ni se maquilla.
