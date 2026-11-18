// Lo de afuera que toca a Colombia: que parte de la comida se importa (FAO) y como se
// movio el precio de los fertilizantes (Banco Mundial) frente al de la comida (SIPSA).

import { mesCorto, porcentaje } from "@/lib/formato";
import type { DatosInternacional } from "@/lib/tipos";

const SERIES = [
  { clave: "comida", nombre: "Comida en las centrales (SIPSA)", clase: "linea-comida" },
  { clave: "Urea", nombre: "Urea, fertilizante (Banco Mundial)", clase: "linea-urea" },
  { clave: "DAP", nombre: "DAP, fertilizante (Banco Mundial)", clase: "linea-dap" },
] as const;

function Indices({ indices }: { indices: DatosInternacional["indices"] }) {
  const ancho = 720, alto = 280, m = { arriba: 16, derecha: 130, abajo: 34, izquierda: 44 };
  const n = indices.periodos.length;
  const valores = SERIES.flatMap((s) => indices[s.clave] ?? []).filter((v): v is number => v !== null);
  const min = Math.min(80, ...valores), max = Math.max(...valores) * 1.05;
  const x = (i: number) => m.izquierda + (i * (ancho - m.izquierda - m.derecha)) / (n - 1);
  const y = (v: number) => alto - m.abajo - ((v - min) * (alto - m.arriba - m.abajo)) / (max - min);

  return (
    <svg className="grafica-detalle" viewBox={`0 0 ${ancho} ${alto}`} role="img"
      aria-label="Precio de la comida y de los fertilizantes desde 2020, base 100 = promedio de 2020">
      {[100, 200, 300].filter((v) => v < max).map((v) => (
        <g key={v}>
          <line className="rejilla" x1={m.izquierda} x2={ancho - m.derecha} y1={y(v)} y2={y(v)} />
          <text className="eje" x={m.izquierda - 6} y={y(v) + 4} textAnchor="end">{v}</text>
        </g>
      ))}
      {indices.periodos.map((p, i) => p % 100 === 1 && (
        <text key={p} className="eje" x={x(i)} y={alto - 12} textAnchor="middle">{Math.floor(p / 100)}</text>
      ))}
      {SERIES.map((s) => {
        const serie = indices[s.clave] ?? [];
        // Un mes sin dato corta la linea (el hueco de 2021 en la comida).
        const partes: string[][] = [[]];
        serie.forEach((v, i) => (v === null ? partes.push([]) : partes[partes.length - 1].push(`${x(i)},${y(v)}`)));
        const iFin = serie.findLastIndex((v) => v !== null);
        return (
          <g key={s.clave} className={s.clase}>
            {partes.filter((t) => t.length > 1).map((t) => <polyline key={t[0]} points={t.join(" ")} />)}
            {iFin >= 0 && (
              <text className="eje etiqueta-linea" x={x(iFin) + 6} y={y(serie[iFin] as number) + 4}>
                {s.clave === "comida" ? "Comida" : s.clave} {Math.round(serie[iFin] as number)}
              </text>
            )}
          </g>
        );
      })}
    </svg>
  );
}

export function Internacional({ datos }: { datos: DatosInternacional }) {
  const { indices } = datos;
  const fin = indices.periodos.length - 1;
  const comidaHoy = indices.comida.findLast((v) => v !== null);
  const masNuestro = datos.dependencia_nuestros[0];

  return (
    <section className="internacional" aria-labelledby="titulo-internacional">
      <h2 id="titulo-internacional">Lo de afuera que toca a Colombia</h2>
      <p className="bajada">
        Los datos internacionales no se quedan en una lista de fuentes: se cruzan con lo nacional para responder
        dos preguntas.
      </p>

      <div className="internacional-rejilla">
        <div className="historia-bloque historia-ancha">
          <h3>¿Los fertilizantes subieron más que la comida?</h3>
          <Indices indices={indices} />
          <ul className="leyenda-lineas">
            {SERIES.map((s) => <li key={s.clave} className={s.clase}><span className="muestra-linea" /> {s.nombre}</li>)}
          </ul>
          <p className="nota">
            Las tres líneas valen 100 en el promedio de 2020, para comparar cosas con unidades distintas (dólares
            por tonelada y pesos por kilo). En {mesCorto(indices.periodos[fin])} la comida estaba en{" "}
            {comidaHoy != null ? Math.round(comidaHoy) : "sin dato"}: {comidaHoy != null ? porcentaje(comidaHoy - 100) : ""} frente
            a 2020. Los fertilizantes son el principal insumo importado del campo; que suban juntos no prueba que uno
            cause el otro.
          </p>
        </div>

        <div className="historia-bloque">
          <h3>¿Cuánto de nuestra comida viene de afuera?</h3>
          <p>
            De los alimentos que sigue este proyecto, el más importado es{" "}
            <strong>{masNuestro?.producto.toLowerCase()}</strong>, con apenas{" "}
            {masNuestro?.dependencia_pct != null ? `${masNuestro.dependencia_pct} %` : "sin dato"} de lo que se consume.
            Frutas, verduras y tubérculos frescos se producen casi todos en el país: su precio depende del clima y de
            las cosechas de aquí más que del dólar.
          </p>
          <table className="tabla-chica">
            <thead><tr><th>Alimento</th><th className="derecha">Importado</th></tr></thead>
            <tbody>
              {datos.dependencia_nuestros.slice(0, 6).map((d) => (
                <tr key={d.producto}><th scope="row">{d.producto}</th><td className="derecha numero">{d.dependencia_pct} %</td></tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="historia-bloque">
          <h3>Lo que más se importa ({datos.anio_fao})</h3>
          <p>Otros alimentos sí vienen casi todos de afuera. Su precio sigue al precio internacional y al dólar.</p>
          <table className="tabla-chica">
            <thead><tr><th>Producto (nombre FAO)</th><th className="derecha">Importado</th></tr></thead>
            <tbody>
              {datos.mas_importados.slice(0, 8).map((d) => (
                <tr key={d.item_fao}><th scope="row">{d.item_fao}</th><td className="derecha numero">{d.dependencia_pct} %</td></tr>
              ))}
            </tbody>
          </table>
          <p className="nota">
            Importado = importaciones ÷ (producción + importaciones − exportaciones). Fuente: FAOSTAT, en toneladas;
            los nombres van en inglés, como los publica la FAO.
          </p>
        </div>
      </div>
    </section>
  );
}
