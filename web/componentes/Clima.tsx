// Las tres piezas del clima: el fenomeno de El Nino, la lluvia que se espera
// y como se mide la lluvia con sensores. No necesitan interaccion: son dibujo fijo.

import { mesCorto, mesLargo } from "@/lib/formato";
import type { Departamento, Nino } from "@/lib/tipos";

const NOMBRE_FASE: Record<string, string> = { "El Nino": "El Niño", "La Nina": "La Niña", Neutral: "Neutral" };
const UMBRAL_FASE = 0.5; // a partir de +-0,5 grados NOAA habla de El Nino o La Nina

const un_decimal = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const grados = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${un_decimal.format(Math.abs(v))} °C`;

/** El Pacifico mes a mes: barras rojas cuando esta caliente (El Nino), azules cuando esta frio. */
export function ElNino({ nino }: { nino: Nino }) {
  const ancho = 640, alto = 220, m = { arriba: 14, derecha: 10, abajo: 30, izquierda: 44 };
  const serie = nino.serie.filter((s): s is { periodo: number; anomalia: number } => s.anomalia !== null);
  const tope = Math.max(2.5, ...serie.map((s) => Math.abs(s.anomalia)));
  const y = (v: number) => m.arriba + ((tope - v) * (alto - m.arriba - m.abajo)) / (2 * tope);
  const paso = (ancho - m.izquierda - m.derecha) / serie.length;
  const fase = NOMBRE_FASE[nino.fase] ?? nino.fase;
  const clase = nino.fase === "El Nino" ? "nino" : nino.fase === "La Nina" ? "nina" : "neutral";

  return (
    <article className="tarjeta-clima">
      <p className="antetitulo">Fenómeno de El Niño · NOAA</p>
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
            <rect key={s.periodo} className={`barra-oni barra-${tipo}`} x={m.izquierda + i * paso + 1.5}
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
        <span className="muestra barra-nino" /> El Niño (más de +0,5 °C)
        <span className="muestra barra-nina" /> La Niña (menos de −0,5 °C)
        <span className="muestra barra-neutral" /> Neutral
      </p>
    </article>
  );
}

/** La lluvia que se espera en los proximos meses: un rango por mes, no un numero solo. */
export function LluviaEsperada({ departamentos }: { departamentos: Departamento[] }) {
  const conPronostico = departamentos.filter((d) => d.lluvia_esperada);
  const tope = Math.max(...conPronostico.flatMap((d) => d.lluvia_esperada!.map((f) => f.lluvioso ?? 0)));
  const alto = 96, ancho = 250, base = 70, margen = 14;

  return (
    <article className="tarjeta-clima">
      <p className="antetitulo">Lluvia esperada · Open-Meteo</p>
      <h3>Cuánto se espera que llueva en los próximos meses</h3>
      <p className="nota">
        Cada barra va del escenario seco al lluvioso (8 de cada 10 escenarios caen ahí) y la raya es el
        escenario central. Debajo, si eso es más o menos de lo normal para ese mes.
      </p>
      <div className="rejilla-lluvia">
        {conPronostico.map((d) => {
          const meses = d.lluvia_esperada!;
          const paso = (ancho - 2 * margen) / meses.length;
          const y = (mm: number) => base - (mm * (base - 8)) / tope;
          return (
            <figure key={d.codigo} className="lluvia-depto">
              <figcaption>{d.nombre}</figcaption>
              <svg viewBox={`0 0 ${ancho} ${alto}`} role="img"
                aria-label={`Lluvia esperada en ${d.nombre}: ${meses.map((f) => `${mesCorto(f.periodo)} ${f.central} mm`).join(", ")}`}>
                <line className="eje-cero" x1={margen} x2={ancho - margen} y1={base} y2={base} />
                {meses.map((f, i) => {
                  const x = margen + i * paso + paso / 2;
                  const menos = (f.frente_a_lo_normal ?? 0) < 0;
                  return (
                    <g key={f.periodo}>
                      <rect className="rango-lluvia" x={x - 9} y={y(f.lluvioso ?? 0)} width={18} rx={4}
                        height={Math.max(y(f.seco ?? 0) - y(f.lluvioso ?? 0), 2)} />
                      <line className="central-lluvia" x1={x - 12} x2={x + 12} y1={y(f.central ?? 0)} y2={y(f.central ?? 0)} />
                      <text className="eje" x={x} y={base + 12} textAnchor="middle">{mesCorto(f.periodo).split(" ")[0]}</text>
                      <text className={`eje ${menos ? "texto-seco" : "texto-lluvia"}`} x={x} y={base + 24} textAnchor="middle">
                        {f.frente_a_lo_normal === null ? "" : `${menos ? "▼" : "▲"}${Math.abs(f.frente_a_lo_normal)}`}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </figure>
          );
        })}
      </div>
      <p className="leyenda-clima">
        <span className="texto-lluvia">▲ más lluvia de lo normal</span>
        <span className="texto-seco">▼ menos lluvia de lo normal</span> · en milímetros por mes
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
      <p className="antetitulo">El sensor · IDEAM</p>
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
