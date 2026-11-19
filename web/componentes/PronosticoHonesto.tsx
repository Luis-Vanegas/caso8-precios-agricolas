// ¿Que tan bien adivina el pronostico? Por producto, el error del modelo frente al de
// suponer que el precio sigue igual. Se muestra donde acierta y donde no.

import type { Fila } from "@/lib/tipos";

const un_decimal = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

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
