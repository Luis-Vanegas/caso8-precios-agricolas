"use client";

// El tablero de semaforos: una fila por producto con su precio, sus dos
// comparaciones (mes pasado y mismo mes del anio pasado), su estado y su pronostico.

import { ArrowDownRight, ArrowUpRight, ChevronDown, ChevronRight, Minus } from "lucide-react";
import { Fragment, useMemo, useState } from "react";

import { Contador } from "@/componentes/Contador";
import { GraficaDetalle, Minigrafica } from "@/componentes/Graficas";
import {
  cambioEsperado, direccion, estadoGeneral, mesLargo, motivoEstado, nivelPrecio,
  NOMBRE_ESTADO, NOMBRE_NIVEL, pesos, porcentaje, UMBRAL_CARO, urgencia,
} from "@/lib/formato";
import type { Direccion } from "@/lib/formato";
import type { Fila, Tablero as DatosTablero } from "@/lib/tipos";

type Orden = "urgencia" | "producto" | "precio" | "mes" | "anio";

const ORDENES: { valor: Orden; texto: string }[] = [
  { valor: "urgencia", texto: "Lo más fuera de lo normal primero" },
  { valor: "mes", texto: "Mayor cambio frente al mes pasado" },
  { valor: "anio", texto: "Mayor cambio frente al año pasado" },
  { valor: "precio", texto: "Precio, de mayor a menor" },
  { valor: "producto", texto: "Producto, de la A a la Z" },
];

function ordenar(filas: Fila[], orden: Orden): Fila[] {
  const copia = [...filas];
  const abs = (v: number | null) => Math.abs(v ?? 0);
  switch (orden) {
    case "producto": return copia.sort((a, b) => a.producto.localeCompare(b.producto, "es"));
    case "precio": return copia.sort((a, b) => (b.precio ?? 0) - (a.precio ?? 0));
    case "mes": return copia.sort((a, b) => abs(b.cambio_mes_pct) - abs(a.cambio_mes_pct));
    case "anio": return copia.sort((a, b) => abs(b.cambio_anio_pct) - abs(a.cambio_anio_pct));
    default: return copia.sort((a, b) => urgencia(b) - urgencia(a));
  }
}

/** El icono de la direccion: sube, baja o se mantiene. Lleva el color; el numero va en tinta. */
function IconoDireccion({ d, grande = false }: { d: Direccion; grande?: boolean }) {
  const Icono = d === "sube" ? ArrowUpRight : d === "baja" ? ArrowDownRight : Minus;
  return (
    <span className={`icono-direccion icono-${d}${grande ? " icono-grande" : ""}`} aria-hidden="true">
      <Icono size={grande ? 22 : 15} strokeWidth={2.4} />
    </span>
  );
}

/** Flecha, porcentaje y color de una comparacion. El color nunca va solo: lleva flecha y signo. */
function Cambio({ valor }: { valor: number | null }) {
  const d = direccion(valor);
  if (d === "sin dato") return <span className="apagado">sin dato</span>;
  return (
    <span className={`cambio cambio-${d}`}>
      <IconoDireccion d={d} />{porcentaje(valor)}
      <span className="solo-lector"> ({d})</span>
    </span>
  );
}

function Estado({ fila }: { fila: Fila }) {
  const estado = estadoGeneral(fila);
  return (
    <span className="estado">
      <span className={`pastilla pastilla-${estado.replace(" ", "-")}`}>{NOMBRE_ESTADO[estado]}</span>
      <span className="motivo">{motivoEstado(fila)}</span>
    </span>
  );
}

/** ¿Esta caro? Color y palabra juntos; debajo, cuanto frente a su precio tipico. */
function Nivel({ fila }: { fila: Fila }) {
  const { nivel, frente_tipico, tipico } = nivelPrecio(fila);
  return (
    <span className="estado" title={tipico !== null ? `Precio típico del último año: ${pesos(tipico)}` : undefined}>
      <span className={`pastilla nivel-${nivel.replace(" ", "-")}`}>{NOMBRE_NIVEL[nivel]}</span>
      {frente_tipico !== null && <span className="motivo">{porcentaje(frente_tipico)} frente a lo de costumbre</span>}
    </span>
  );
}

function ProximoMes({ fila }: { fila: Fila }) {
  const esperado = cambioEsperado(fila);
  const proximo = fila.pronostico?.meses[0];
  if (!proximo || esperado === null) return <span className="apagado">sin pronóstico</span>;
  const d = direccion(esperado);
  return (
    <span className="proximo">
      <span className={`cambio cambio-${d}`}>
        <IconoDireccion d={d} />
        {d === "igual" ? "se mantiene" : d === "sube" ? "sube" : "baja"}
      </span>
      <span className="numero">≈ {pesos(proximo.valor)}</span>
    </span>
  );
}

function Confianza({ fila }: { fila: Fila }) {
  if (!fila.pronostico) return <span className="apagado">—</span>;
  return fila.pronostico.confiable
    ? <span className="confianza confianza-alta">Alta</span>
    : <span className="confianza confianza-baja">Baja</span>;
}

function Detalle({ fila, datos }: { fila: Fila; datos: DatosTablero }) {
  const p = fila.pronostico;
  return (
    <div className="detalle">
      <div className="detalle-grafica">
        <h3>{fila.producto}: precio por kilo, {fila.mercado === "Nacional" ? "promedio del país" : fila.mercado}</h3>
        <GraficaDetalle periodos={datos.periodos} serie={fila.serie} pronostico={p} />
        <p className="nota">
          La línea oscura es el precio observado cada mes. {p
            ? "A la derecha de «hoy», la línea azul es el pronóstico y la franja es el rango donde debería caer el precio (8 de cada 10 veces en el pasado cayó ahí)."
            : "El pronóstico solo se calcula para el promedio del país."}
          {" "}Donde la línea se corta, no hubo dato ese mes.
        </p>
      </div>

      {p && (
        <div className="detalle-pronostico">
          <h3>Lo que viene</h3>
          <table className="tabla-chica">
            <thead>
              <tr><th scope="col">Mes</th><th scope="col">Precio esperado</th><th scope="col">Entre</th></tr>
            </thead>
            <tbody>
              {p.meses.map((mes) => (
                <tr key={mes.periodo}>
                  <th scope="row">{mesLargo(mes.periodo)}</th>
                  <td className="numero">{pesos(mes.valor)}</td>
                  <td className="numero">{pesos(mes.minimo)} y {pesos(mes.maximo)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className={`aviso ${p.confiable ? "aviso-bien" : "aviso-cuidado"}`}>
            <strong>Confianza {p.confiable ? "alta" : "baja"}.</strong>{" "}
            {p.confiable
              ? `En las pruebas contra los últimos dos años, este pronóstico se equivocó en promedio ${porcentaje(p.error_modelo_pct).replace("+", "")}; suponer que el precio seguía igual se equivocó ${porcentaje(p.error_ingenuo_pct).replace("+", "")}.`
              : `Para este producto, el modelo no logró ser mejor que suponer que el precio sigue igual (se equivocó ${porcentaje(p.error_modelo_pct).replace("+", "")} contra ${porcentaje(p.error_ingenuo_pct).replace("+", "")}). Tómalo como una referencia, no como un anuncio.`}
          </p>
        </div>
      )}
    </div>
  );
}

export function Tablero({ datos }: { datos: DatosTablero }) {
  const [mercado, setMercado] = useState("Nacional");
  const [orden, setOrden] = useState<Orden>("urgencia");
  const [abierto, setAbierto] = useState<string | null>(null);

  const filas = useMemo(
    () => ordenar(datos.filas.filter((f) => f.mercado === mercado), orden),
    [datos.filas, mercado, orden],
  );
  const esNacional = mercado === "Nacional";

  const suben = filas.filter((f) => direccion(f.cambio_mes_pct) === "sube").length;
  const bajan = filas.filter((f) => direccion(f.cambio_mes_pct) === "baja").length;
  const fuera = filas.filter((f) => ["amarilla", "roja"].includes(estadoGeneral(f))).length;
  const subiran = filas.filter((f) => direccion(cambioEsperado(f)) === "sube").length;
  const caros = filas.filter((f) => nivelPrecio(f).nivel === "caro").length;
  const baratos = filas.filter((f) => nivelPrecio(f).nivel === "barato").length;

  return (
    <section aria-labelledby="titulo-tablero">
      <div className="resumen">
        <div className="cifra">
          <span className="cifra-numero"><IconoDireccion d="sube" grande /><Contador valor={suben} /></span>
          <span className="cifra-texto">subieron frente al mes pasado</span>
        </div>
        <div className="cifra">
          <span className="cifra-numero"><IconoDireccion d="baja" grande /><Contador valor={bajan} /></span>
          <span className="cifra-texto">bajaron frente al mes pasado</span>
        </div>
        <div className="cifra">
          <span className="cifra-numero"><span className="pastilla nivel-caro">Caro</span><Contador valor={caros} /></span>
          <span className="cifra-texto">están más caros que de costumbre</span>
        </div>
        <div className="cifra">
          <span className="cifra-numero"><span className="pastilla nivel-barato">Barato</span><Contador valor={baratos} /></span>
          <span className="cifra-texto">están más baratos que de costumbre</span>
        </div>
        <div className="cifra">
          <span className="cifra-numero"><Contador valor={fuera} /></span>
          <span className="cifra-texto">se movieron más de lo normal</span>
        </div>
        {esNacional && (
          <div className="cifra">
            <span className="cifra-numero"><IconoDireccion d="sube" grande /><Contador valor={subiran} /></span>
            <span className="cifra-texto">se espera que suban el próximo mes</span>
          </div>
        )}
      </div>

      <div className="controles">
        <label>
          <span>Dónde</span>
          <select value={mercado} onChange={(e) => { setMercado(e.target.value); setAbierto(null); }}>
            {datos.mercados.map((m) => (
              <option key={m} value={m}>{m === "Nacional" ? "Todo el país (promedio)" : m}</option>
            ))}
          </select>
        </label>
        <label>
          <span>Ordenar por</span>
          <select value={orden} onChange={(e) => setOrden(e.target.value as Orden)}>
            {ORDENES.map((o) => <option key={o.valor} value={o.valor}>{o.texto}</option>)}
          </select>
        </label>
      </div>

      <h2 id="titulo-tablero" className="solo-lector">
        Precios de {datos.ultimo_mes_texto} en {esNacional ? "todo el país" : mercado}
      </h2>
      <table className="tablero">
        <thead>
          <tr>
            <th scope="col">Producto</th>
            <th scope="col" className="derecha">Precio por kilo</th>
            <th scope="col" className="derecha">Frente al mes pasado</th>
            <th scope="col" className="derecha">Frente a hace un año</th>
            <th scope="col">¿Está caro?</th>
            <th scope="col">Estado</th>
            <th scope="col">Últimos 12 meses</th>
            {esNacional && <th scope="col">Próximo mes</th>}
            {esNacional && <th scope="col">Confianza</th>}
          </tr>
        </thead>
        <tbody>
          {filas.map((fila, posicion) => {
            const estaAbierto = abierto === fila.producto;
            return (
              <Fragment key={fila.producto}>
                <tr className={estaAbierto ? "fila fila-abierta" : "fila"}
                  style={{ animationDelay: `${Math.min(posicion, 14) * 28}ms` }}>
                  <th scope="row" data-titulo="Producto">
                    <button type="button" className="boton-producto" aria-expanded={estaAbierto}
                      onClick={() => setAbierto(estaAbierto ? null : fila.producto)}>
                      <span className="flecha-abrir" aria-hidden="true">{estaAbierto ? <ChevronDown size={16} /> : <ChevronRight size={16} />}</span>
                      {fila.producto}
                    </button>
                  </th>
                  <td className="derecha numero" data-titulo="Precio por kilo">{pesos(fila.precio)}</td>
                  <td className="derecha" data-titulo="Frente al mes pasado"><Cambio valor={fila.cambio_mes_pct} /></td>
                  <td className="derecha" data-titulo="Frente a hace un año"><Cambio valor={fila.cambio_anio_pct} /></td>
                  <td data-titulo="¿Está caro?"><Nivel fila={fila} /></td>
                  <td data-titulo="Estado"><Estado fila={fila} /></td>
                  <td data-titulo="Últimos 12 meses"><Minigrafica serie={fila.serie} /></td>
                  {esNacional && <td data-titulo="Próximo mes"><ProximoMes fila={fila} /></td>}
                  {esNacional && <td data-titulo="Confianza"><Confianza fila={fila} /></td>}
                </tr>
                {estaAbierto && (
                  <tr className="fila-detalle">
                    <td colSpan={esNacional ? 9 : 7}><Detalle fila={fila} datos={datos} /></td>
                  </tr>
                )}
              </Fragment>
            );
          })}
        </tbody>
      </table>
      <p className="nota">
        <strong>¿Está caro?</strong> compara el precio de hoy con su precio de costumbre: la mediana de los 12 meses
        anteriores. Más de {UMBRAL_CARO} % por encima es caro y más de {UMBRAL_CARO} % por debajo es barato. Ese{" "}
        {UMBRAL_CARO} % es una convención para leer la tabla, no un resultado estadístico. El <strong>estado</strong>{" "}
        responde otra cosa: si el movimiento es raro para ese producto.
      </p>
      {!esNacional && (
        <p className="nota">El pronóstico solo se calcula para el promedio del país. Elige «Todo el país» para verlo.</p>
      )}
    </section>
  );
}
