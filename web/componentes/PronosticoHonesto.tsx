// ¿Que tan bien adivina el pronostico? Por producto, el error del modelo frente al de
// suponer que el precio sigue igual. Se muestra donde acierta y donde no.

import type { Fila } from "@/lib/tipos";

// En GitHub Pages la web vive en una subcarpeta: las imagenes la necesitan en la ruta.
const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

// Como trabaja el modelo (src/indicators/pronostico.py), en cuatro pasos.
const PASOS = [
  {
    titulo: "Qué mira",
    texto: "La temporada (cada mes del año tiene su cambio típico), cuánto cambió el precio el último mes, la fuerza de El Niño y la lluvia en la zona donde se cultiva.",
  },
  {
    titulo: "Cómo calcula",
    texto: "Una regresión lineal: busca cuánto pesa cada una de esas pistas en el cambio del precio, con toda la historia desde 2020. Pronostica a 1, 2 y 3 meses.",
  },
  {
    titulo: "Cómo se pone a prueba",
    texto: "En cada uno de los últimos 24 meses se le pide adivinar el mes siguiente usando solo lo que se sabía en ese momento, y se mide cuánto se equivocó.",
  },
  {
    titulo: "Cuándo se usa",
    texto: "Solo si se equivoca al menos 5 % menos que la apuesta simple. Si no, se muestra la apuesta simple y se dice. La franja de cada pronóstico sale de sus errores reales en la prueba.",
  },
];

const un_decimal =new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

function Grupo({ titulo, filas, tope }: { titulo: string; filas: Fila[]; tope: number }) {
  return (
    <div className="pronostico-grupo">
      <h3>{titulo} <span className="apagado">({filas.length})</span></h3>
      <ul className="errores">
        {filas.map((f) => {
          const p = f.pronostico!;
          return (
            <li key={f.producto}>
              <span className="errores-nombre">{f.producto}</span>
              <span className="errores-barras" aria-hidden="true">
                <span className="error-modelo" style={{ width: `${((p.error_modelo_pct ?? 0) / tope) * 100}%` }} />
                <span className="error-ingenuo" style={{ width: `${((p.error_ingenuo_pct ?? 0) / tope) * 100}%` }} />
              </span>
              <span className="errores-cifras numero">
                {un_decimal.format(p.error_modelo_pct ?? 0)} % · {un_decimal.format(p.error_ingenuo_pct ?? 0)} %
              </span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export function PronosticoHonesto({ nacionales }: { nacionales: Fila[] }) {
  const con = nacionales.filter((f) => f.pronostico?.error_modelo_pct != null && f.pronostico.error_ingenuo_pct != null);
  const orden = (a: Fila, b: Fila) => (a.pronostico!.error_modelo_pct ?? 0) - (b.pronostico!.error_modelo_pct ?? 0);
  const acierta = con.filter((f) => f.pronostico!.confiable).sort(orden);
  const no = con.filter((f) => !f.pronostico!.confiable).sort(orden);
  const tope = Math.max(...con.flatMap((f) => [f.pronostico!.error_modelo_pct ?? 0, f.pronostico!.error_ingenuo_pct ?? 0]));

  return (
    <section className="pronostico-honesto" aria-labelledby="titulo-pronostico">
      <h2 id="titulo-pronostico">¿Qué tan bien adivina el pronóstico?</h2>
      <p className="bajada">
        Antes de mostrar un pronóstico lo pusimos a prueba: durante los últimos dos años, mes a mes, se le pidió
        adivinar el precio del mes siguiente sin dejarlo ver el futuro. Luego se comparó su error con el de la
        apuesta más simple: <em>el precio sigue igual</em>. Solo en <strong>{acierta.length} de {con.length}</strong>{" "}
        alimentos el modelo se equivoca claramente menos.
      </p>
      <h3 className="subtitulo-pronostico">Cómo funciona</h3>
      <ol className="pasos pasos-ancho">
        {PASOS.map((p, i) => (
          <li key={p.titulo} style={{ animationDelay: `${i * 90}ms` }}>
            <span className="paso-numero">{i + 1}</span>
            <strong>{p.titulo}</strong>
            <span>{p.texto}</span>
          </li>
        ))}
      </ol>
      <figure className="figura-prueba">
        {/* En celular la imagen queda chica: tocarla la abre en grande. */}
        <a href={`${BASE}/figuras/pronostico_ejemplo.png`} target="_blank" rel="noopener">
        {/* La web es exportacion estatica (GitHub Pages): next/image no puede optimizar sin servidor. */}
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={`${BASE}/figuras/pronostico_ejemplo.png`}
          alt="Precio del mango tommy de 2023 a 2026 con lo que el modelo habría pronosticado cada mes de la prueba y el pronóstico de los próximos tres meses con su franja"
          width={1650}
          height={810}
          loading="lazy"
        />
        </a>
        <figcaption>
          Ejemplo con el mango tommy, el alimento donde el modelo más acierta. Los puntos azules son la prueba: lo
          que habría dicho un mes antes, sin ver el futuro. Cerca de la línea negra, acertó; en los picos de precio
          exageró la subida. Datos a octubre de 2026.
        </figcaption>
      </figure>
      <h3 className="subtitulo-pronostico">El resultado, alimento por alimento</h3>
      <figure className="figura-prueba">
        <a href={`${BASE}/figuras/modelo_vs_ingenuo.png`} target="_blank" rel="noopener">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={`${BASE}/figuras/modelo_vs_ingenuo.png`}
            alt="A la izquierda, error del modelo frente al de la apuesta simple para cada alimento; a la derecha, cuántos alimentos usan la regresión, el ingenuo estacional o el ingenuo sin cambio a 1, 2 y 3 meses"
            width={1800}
            height={810}
            loading="lazy"
          />
        </a>
        <figcaption>
          Izquierda: cada punto es un alimento. Si queda debajo de la línea punteada, el modelo se equivoca al
          menos 5 % menos que la apuesta simple y se usa (azul); si no, se usa la apuesta simple (gris). Derecha:
          entre más lejos se pronostica, menos alimentos usan el modelo y más gana la temporada. Datos a octubre
          de 2026.
        </figcaption>
      </figure>
      <div className="leyenda-errores" aria-hidden="true">
        <span><span className="muestra error-modelo" /> error del modelo</span>
        <span><span className="muestra error-ingenuo" /> error de «sigue igual»</span>
        <span className="apagado">error típico de un mes, en % del precio · más corta es mejor</span>
      </div>
      <div className="pronostico-rejilla">
        <Grupo titulo="Aquí el pronóstico ayuda" filas={acierta} tope={tope} />
        <Grupo titulo="Aquí no hay que fiarse: se muestra como referencia" filas={no} tope={tope} />
      </div>
      <p className="nota">
        El modelo usa la temporada, cómo venía el precio, El Niño y la lluvia en la zona de cultivo. Que en la
        mayoría no le gane a «sigue igual» es un resultado, no un error escondido: el precio de un alimento de un
        mes al otro es muy difícil de adivinar, y aquí se mide en vez de prometerlo.
      </p>
    </section>
  );
}
