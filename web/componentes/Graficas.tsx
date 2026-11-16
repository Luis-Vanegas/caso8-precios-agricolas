// Las dos graficas del tablero, dibujadas en SVG sin librerias:
// la minigrafica de cada fila y la grafica grande del detalle.

import { mesCorto, pesos } from "@/lib/formato";
import type { Pronostico } from "@/lib/tipos";

/** Convierte una serie con huecos en tramos de linea: un mes sin dato corta la linea. */
function tramos(puntos: ({ x: number; y: number } | null)[]): string[] {
  const salida: string[] = [];
  let actual: string[] = [];
  for (const p of puntos) {
    if (p === null) {
      if (actual.length > 1) salida.push(actual.join(" "));
      actual = [];
    } else {
      actual.push(`${p.x.toFixed(1)},${p.y.toFixed(1)}`);
    }
  }
  if (actual.length > 1) salida.push(actual.join(" "));
  return salida;
}

/** Minigrafica de los ultimos 12 meses. Es decorativa: el dato exacto esta en la fila. */
export function Minigrafica({ serie }: { serie: (number | null)[] }) {
  const ultimos = serie.slice(-12);
  const valores = ultimos.filter((v): v is number => v !== null);
  if (valores.length < 2) return <span className="apagado">sin dato</span>;

  const ancho = 120, alto = 32, margen = 3;
  const min = Math.min(...valores), max = Math.max(...valores);
  const puntos = ultimos.map((v, i) =>
    v === null ? null : {
      x: margen + (i * (ancho - 2 * margen)) / (ultimos.length - 1),
      y: max === min ? alto / 2 : alto - margen - ((v - min) * (alto - 2 * margen)) / (max - min),
    });
  const ultimo = puntos[puntos.length - 1];

  return (
    <svg className="minigrafica" viewBox={`0 0 ${ancho} ${alto}`} width={ancho} height={alto} aria-hidden="true">
      {tramos(puntos).map((d) => <polyline key={d} points={d} />)}
      {ultimo && <circle cx={ultimo.x} cy={ultimo.y} r="2.5" />}
    </svg>
  );
}

interface PropsDetalle {
  periodos: number[];
  serie: (number | null)[];
  pronostico: Pronostico | null;
}

/** Precio observado (izquierda de "hoy") y pronostico con su banda (derecha). */
export function GraficaDetalle({ periodos, serie, pronostico }: PropsDetalle) {
  const futuros = pronostico?.meses ?? [];
  const total = periodos.length + futuros.length;
  const ancho = 720, alto = 280;
  const m = { arriba: 16, derecha: 16, abajo: 34, izquierda: 62 };

  const todos = [
    ...serie.filter((v): v is number => v !== null),
    ...futuros.flatMap((f) => [f.valor, f.minimo, f.maximo]).filter((v): v is number => v !== null),
  ];
  if (todos.length < 2) return <p className="apagado">No hay precios suficientes para dibujar la gráfica.</p>;

  // El eje arranca un poco por debajo del minimo para que la linea no toque el borde.
  const min = Math.min(...todos) * 0.92, max = Math.max(...todos) * 1.05;
  const x = (i: number) => m.izquierda + (i * (ancho - m.izquierda - m.derecha)) / (total - 1);
  const y = (v: number) => alto - m.abajo - ((v - min) * (alto - m.arriba - m.abajo)) / (max - min);

  const observados = serie.map((v, i) => (v === null ? null : { x: x(i), y: y(v) }));
  const iHoy = periodos.length - 1;
  const precioHoy = serie[iHoy];

  // La linea del pronostico arranca en el precio de hoy para que se vea de donde sale.
  const lineaFutura = [
    ...(precioHoy !== null ? [{ x: x(iHoy), y: y(precioHoy) }] : []),
    ...futuros.flatMap((f, k) => (f.valor === null ? [] : [{ x: x(iHoy + 1 + k), y: y(f.valor) }])),
  ];
  const banda = futuros.every((f) => f.minimo !== null && f.maximo !== null) && precioHoy !== null
    ? [
        `${x(iHoy)},${y(precioHoy)}`,
        ...futuros.map((f, k) => `${x(iHoy + 1 + k)},${y(f.maximo as number)}`),
        ...futuros.map((f, k) => `${x(iHoy + 1 + k)},${y(f.minimo as number)}`).reverse(),
      ].join(" ")
    : null;

  const marcasY = [0, 1, 2, 3].map((k) => min + ((max - min) * k) / 3);
  const etiquetas = [...periodos, ...futuros.map((f) => f.periodo)];
  const cadaCuanto = Math.ceil(total / 7);

  return (
    <svg className="grafica-detalle" viewBox={`0 0 ${ancho} ${alto}`} role="img"
      aria-label={`Precio de los últimos ${periodos.length} meses${futuros.length ? " y pronóstico a 3 meses" : ""}`}>
      {marcasY.map((v) => (
        <g key={v}>
          <line className="rejilla" x1={m.izquierda} x2={ancho - m.derecha} y1={y(v)} y2={y(v)} />
          <text className="eje" x={m.izquierda - 8} y={y(v) + 4} textAnchor="end">{pesos(Math.round(v))}</text>
        </g>
      ))}
      {etiquetas.map((p, i) => i % cadaCuanto === 0 && (
        <text key={p} className="eje" x={x(i)} y={alto - 12} textAnchor="middle">{mesCorto(p)}</text>
      ))}

      {banda && <polygon className="banda" points={banda} />}
      {tramos(observados).map((d) => <polyline key={d} className="observado" points={d} />)}
      {lineaFutura.length > 1 && (
        <polyline className="futuro" points={lineaFutura.map((p) => `${p.x},${p.y}`).join(" ")} />
      )}
      {lineaFutura.slice(1).map((p) => <circle key={p.x} className="punto-futuro" cx={p.x} cy={p.y} r="4" />)}

      <line className="hoy" x1={x(iHoy)} x2={x(iHoy)} y1={m.arriba} y2={alto - m.abajo} />
      <text className="eje hoy-texto" x={x(iHoy) - 6} y={m.arriba + 10} textAnchor="end">hoy</text>
    </svg>
  );
}
