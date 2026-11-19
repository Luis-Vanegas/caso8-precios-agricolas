"use client";

// La historia de un alimento: todo su precio desde 2020, el pronostico, en que meses
// suele estar mas barato y como esta este mes frente al mismo mes de otros anios.

import { useState } from "react";

import { GraficaDetalle } from "@/componentes/Graficas";
import { mesLargo, pesos, porcentaje } from "@/lib/formato";
import type { DatosHistoria, Fila } from "@/lib/tipos";

const MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];
const MESES_LARGOS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
  "septiembre", "octubre", "noviembre", "diciembre"];

interface Props {
  historia: DatosHistoria;
  /** Las filas "Nacional" del tablero: de ahi sale el pronostico. */
  nacionales: Fila[];
}

function Estacionalidad({ valores, anios }: { valores: (number | null)[]; anios: number }) {
  const conDato = valores.map((v, i) => ({ v, i })).filter((x): x is { v: number; i: number } => x.v !== null);
  if (conDato.length < 6) return <p className="apagado">Todavía no hay años suficientes para ver un patrón.</p>;
  const barato = conDato.reduce((a, b) => (b.v < a.v ? b : a));
  const caro = conDato.reduce((a, b) => (b.v > a.v ? b : a));
  const tope = Math.max(...conDato.map((x) => Math.abs(x.v)), 5);

  return (
    <div>
      <p className="historia-resumen">
        Suele estar <strong className="cambio-baja">más barato en {MESES_LARGOS[barato.i]}</strong> ({porcentaje(barato.v)})
        y <strong className="cambio-sube">más caro en {MESES_LARGOS[caro.i]}</strong> ({porcentaje(caro.v)}),
        frente a su promedio del año.
      </p>
      <ol className="estacional" aria-label="Precio de cada mes frente al promedio del año">
        {valores.map((v, i) => (
          <li key={i} title={v === null ? "sin dato" : porcentaje(v)}>
            <span className="estacional-columna">
              {v !== null && (
                <span className={`estacional-barra ${v >= 0 ? "estacional-caro" : "estacional-barato"}`}
                  style={{ height: `${(Math.abs(v) / tope) * 50}%` }} />
              )}
            </span>
            <span className="estacional-mes">{MESES[i]}</span>
          </li>
        ))}
      </ol>
      <p className="nota">
        Cada barra es la mediana de {anios} años: cuánto más caro (rojo, arriba) o más barato (azul, abajo)
        estuvo ese mes frente al promedio de su año. Es un patrón del pasado, no una promesa.
      </p>
    </div>
  );
}

export function HistoriaAlimento({ historia, nacionales }: Props) {
  const nombres = historia.productos.map((p) => p.producto).sort((a, b) => a.localeCompare(b, "es"));
  const [producto, setProducto] = useState(nombres.includes("Tomate") ? "Tomate" : nombres[0]);
  const datos = historia.productos.find((p) => p.producto === producto)!;
  const fila = nacionales.find((f) => f.producto === producto) ?? null;

  // El mismo mes del calendario en cada anio: compara sin que la temporada confunda.
  const iUltimo = datos.serie.findLastIndex((v) => v !== null);
  const ultimoPeriodo = historia.periodos[iUltimo];
  const mismoMes = historia.periodos
    .map((p, i) => ({ p, v: datos.serie[i] }))
    .filter((x) => x.p % 100 === ultimoPeriodo % 100);
  const hoy = datos.serie[iUltimo];

  return (
    <section className="historia" aria-labelledby="titulo-historia">
      <h2 id="titulo-historia">La historia de un alimento</h2>
      <p className="nota">Precio nacional (la mediana de las centrales mayoristas), desde que hay datos.</p>

      <div className="controles">
        <label>
          Alimento
          <select value={producto} onChange={(e) => setProducto(e.target.value)}>
            {nombres.map((n) => <option key={n}>{n}</option>)}
          </select>
        </label>
      </div>

      <div className="historia-rejilla">
        <div className="historia-bloque historia-ancha">
          <h3>Su precio, mes a mes, y lo que se espera</h3>
          <GraficaDetalle periodos={historia.periodos} serie={datos.serie} pronostico={fila?.pronostico ?? null} />
          <p className="nota">
            El corte de 2021 es un hueco real: el DANE no publicó esos meses y no se rellena.
            {fila?.pronostico
              ? fila.pronostico.confiable
                ? " La línea punteada es el pronóstico; en este alimento acertó más que suponer que el precio seguía igual."
                : " La línea punteada es el pronóstico, pero en este alimento no acertó más que suponer que el precio seguía igual: tómalo solo como referencia."
              : ""}
          </p>
        </div>

        <div className="historia-bloque">
          <h3>¿En qué meses suele estar más barato?</h3>
          <Estacionalidad valores={datos.estacionalidad} anios={datos.anios_estacionalidad} />
        </div>

        <div className="historia-bloque">
          <h3>{MESES_LARGOS[(ultimoPeriodo % 100) - 1][0].toUpperCase() + MESES_LARGOS[(ultimoPeriodo % 100) - 1].slice(1)} de cada año</h3>
          <table className="tabla-chica">
            <thead><tr><th>Año</th><th className="derecha">Precio por kilo</th><th className="derecha">Hoy frente a ese año</th></tr></thead>
            <tbody>
              {mismoMes.map(({ p, v }) => (
                <tr key={p}>
                  <th scope="row">{Math.floor(p / 100)}</th>
                  <td className="derecha numero">{pesos(v)}</td>
                  <td className="derecha numero">
                    {p === ultimoPeriodo ? "hoy" : v && hoy ? porcentaje((hoy / v - 1) * 100) : "sin dato"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="nota">Comparar el mismo mes evita confundir una subida con la temporada. Datos hasta {mesLargo(ultimoPeriodo)}.</p>
        </div>
      </div>
    </section>
  );
}
