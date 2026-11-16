// Tres piezas del clima: el fenomeno de El Nino, la lluvia que se espera y
// como se mide la lluvia con sensores. No necesitan interaccion: son dibujo fijo.

import { CloudRain, Radio, Thermometer } from "lucide-react";

import { mesCorto, mesLargo } from "@/lib/formato";
import type { Departamento, Nino } from "@/lib/tipos";

const NOMBRE_FASE: Record<string, string> = { "El Nino": "El Niño", "La Nina": "La Niña", Neutral: "Neutral" };
const UMBRAL_FASE = 0.5; // a partir de +-0,5 grados NOAA habla de El Nino o La Nina

const un_decimal = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const grados = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${un_decimal.format(Math.abs(v))} °C`;

/** El Pacifico mes a mes: barras rojas cuando esta caliente (El Nino), azules cuando esta frio. */
export function ElNino({ nino }: { nino: Nino }) {
  const ancho = 640, alto = 230, m = { arriba: 14, derecha: 10, abajo: 30, izquierda: 48 };
  const serie = nino.serie.filter((s): s is { periodo: number; anomalia: number } => s.anomalia !== null);
  const tope = Math.max(2.5, ...serie.map((s) => Math.abs(s.anomalia)));
  const y = (v: number) => m.arriba + ((tope - v) * (alto - m.arriba - m.abajo)) / (2 * tope);
  const paso = (ancho - m.izquierda - m.derecha) / serie.length;
  const fase = NOMBRE_FASE[nino.fase] ?? nino.fase;
  const clase = nino.fase === "El Nino" ? "nino" : nino.fase === "La Nina" ? "nina" : "neutral";

  return (
    <article className="tarjeta-clima">
      <p className="antetitulo con-icono"><Thermometer size={15} aria-hidden="true" /> Fenómeno de El Niño · NOAA</p>
      <h3>
        Hoy hay <span className={`fase fase-${clase}`}>{fase}</span>
        {nino.anomalia !== null && <>: el Pacífico está {grados(nino.anomalia)} frente a lo normal</>}
      </h3>
      <p className="nota">
        Con El Niño, en la mayor parte de Colombia suele llover menos; con La Niña, más. Dato de{" "}
        {mesLargo(nino.periodo)}{nino.provisional ? ", todavía provisional" : ""}.
      </p>
      <svg viewBox={`0 0 ${ancho} ${alto}`} className="grafica-clima" role="img"
        aria-label={`Temperatura del Pacífico frente a lo normal en los últimos ${serie.length} meses`}>
        {[-2, -1, 0, 1, 2].map((v) => (
          <g key={v}>
            <line className={v === 0 ? "eje-cero" : "rejilla"} x1={m.izquierda} x2={ancho - m.derecha} y1={y(v)} y2={y(v)} />
            <text className="eje" x={m.izquierda - 8} y={y(v) + 4} textAnchor="end">{grados(v)}</text>
          </g>
        ))}
        {serie.map((s, i) => {
          const tipo = s.anomalia >= UMBRAL_FASE ? "nino" : s.anomalia <= -UMBRAL_FASE ? "nina" : "neutral";
          const arriba = Math.min(y(s.anomalia), y(0));
          return (
            <rect key={s.periodo} className={`barra-oni barra-${tipo}`} x={m.izquierda + i * paso + 1.5} rx={2}
              y={arriba} width={paso - 3} height={Math.max(Math.abs(y(s.anomalia) - y(0)), 1)}
              style={{ animationDelay: `${i * 22}ms`, transformOrigin: `0 ${y(0)}px` }}>
              <title>{`${mesLargo(s.periodo)}: ${grados(s.anomalia)}`}</title>
            </rect>
          );
        })}
        {serie.map((s, i) => i % 6 === 0 && (
          <text key={s.periodo} className="eje" x={m.izquierda + i * paso + paso / 2} y={alto - 10} textAnchor="middle">
            {mesCorto(s.periodo)}
          </text>
        ))}
      </svg>
      <p className="leyenda-clima">
        <span><span className="muestra barra-nino" />El Niño (más de +0,5 °C)</span>
        <span><span className="muestra barra-nina" />La Niña (menos de −0,5 °C)</span>
        <span><span className="muestra barra-neutral" />Neutral</span>
      </p>
    </article>
  );
}

/**
 * La lluvia que se espera, como una tabla: una fila por departamento y una
 * columna por mes. El numero es el escenario central; la barra, el rango.
 */
export function LluviaEsperada({ departamentos }: { departamentos: Departamento[] }) {
  const filas = departamentos.filter((d) => d.lluvia_esperada);
  if (filas.length === 0) return null;
  const mesesTabla = filas[0].lluvia_esperada!.map((f) => f.periodo);
  const tope = Math.max(...filas.flatMap((d) => d.lluvia_esperada!.map((f) => f.lluvioso ?? 0)));

  return (
    <article className="tarjeta-clima">
      <p className="antetitulo con-icono"><CloudRain size={15} aria-hidden="true" /> Lluvia esperada · Open-Meteo</p>
      <h3>Cuánto se espera que llueva en los próximos meses</h3>
      <p className="nota">
        Milímetros de lluvia en el mes. El número es el escenario más probable y la barra muestra el
        rango: del escenario seco al lluvioso (8 de cada 10 escenarios caen ahí). Celda más oscura, más lluvia.
      </p>
      <div className="tabla-desliza">
        <table className="lluvia-tabla">
          <thead>
            <tr>
              <th scope="col">Departamento</th>
              {mesesTabla.map((p) => <th key={p} scope="col">{mesCorto(p)}</th>)}
            </tr>
          </thead>
          <tbody>
            {filas.map((d) => (
              <tr key={d.codigo}>
                <th scope="row">{d.nombre}</th>
                {d.lluvia_esperada!.map((f) => {
                  const central = f.central ?? 0, seco = f.seco ?? 0, lluvioso = f.lluvioso ?? 0;
                  // La intensidad del fondo sigue la cantidad de lluvia (un solo color, de claro a oscuro).
                  const intensidad = Math.round((central / tope) * 100);
                  return (
                    <td key={f.periodo} className={intensidad > 55 ? "celda-oscura" : undefined}
                      style={{ background: `color-mix(in srgb, var(--azul) ${Math.round(intensidad * 0.85)}%, var(--superficie))` }}
                      title={`${d.nombre}, ${mesLargo(f.periodo)}: entre ${seco} y ${lluvioso} mm; lo más probable, ${central} mm`}>
                      <span className="lluvia-valor">{central}</span>
                      <span className="lluvia-rango" aria-hidden="true">
                        <span style={{ left: `${(seco / tope) * 100}%`, width: `${Math.max(((lluvioso - seco) / tope) * 100, 3)}%` }} />
                      </span>
                      <span className="lluvia-entre">{seco}–{lluvioso}</span>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="nota">
        <strong>Por qué no decimos «más» o «menos de lo normal».</strong> Este pronóstico sale de un modelo
        y lo que llamamos normal sale de otro. Al restarlos, la diferencia mide más el desajuste entre
        modelos que la lluvia: daba cifras imposibles. Mientras no se corrija, se muestra solo lo esperado.
      </p>
    </article>
  );
}

/** Como se convierte la lectura de un sensor en el dato que pinta el mapa. */
export function ComoMideElSensor({ estaciones, departamentos }: { estaciones: number; departamentos: number }) {
  const pasos = [
    { titulo: "La estación mide", texto: "Un sensor automático del IDEAM registra la lluvia y la temperatura cada 10 minutos o cada hora." },
    { titulo: "Se resume por mes", texto: "El IDEAM publica unos 116 millones de lecturas. Se suman por estación y mes, y solo cuentan los meses con lecturas suficientes." },
    { titulo: "Se junta por departamento", texto: "De las estaciones válidas de cada departamento se toma el valor del medio (la mediana), para que una estación dañada no arrastre el dato." },
    { titulo: "Se compara con lo normal", texto: "A la lluvia del mes se le resta lo que suele llover en ese mismo mes. Esa diferencia es la que pinta el mapa." },
  ];
  return (
    <article className="tarjeta-clima">
      <p className="antetitulo con-icono"><Radio size={15} aria-hidden="true" /> El sensor · IDEAM</p>
      <h3>
        {estaciones} estaciones en {departamentos} departamentos miden la lluvia en tierra
      </h3>
      <ol className="pasos">
        {pasos.map((p, i) => (
          <li key={p.titulo} style={{ animationDelay: `${i * 90}ms` }}>
            <span className="paso-numero">{i + 1}</span>
            <strong>{p.titulo}</strong>
            <span>{p.texto}</span>
          </li>
        ))}
      </ol>
      <p className="nota">
        <strong>Para qué se usa.</strong> El sensor muestra el clima reciente medido en el terreno. Para
        estudiar cómo afecta la lluvia a los precios se usa la serie de la NASA (satélite), porque llega
        desde 1991 y los sensores de la base empiezan en 2020. Son dos miradas del mismo fenómeno: una
        desde el suelo y otra desde el espacio.
      </p>
    </article>
  );
}
