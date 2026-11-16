"use client";

// El mapa de Colombia: cada departamento se pinta segun como va su precio o su
// lluvia, mes a mes. Se puede reproducir como una pelicula de los ultimos 12 meses.

import { Box, CloudRain, Map as IconoMapa, Pause, Play, Tag } from "lucide-react";
import dynamic from "next/dynamic";
import { useEffect, useMemo, useState } from "react";

import { mesCorto, mesLargo, porcentaje } from "@/lib/formato";
import { ALTO, ANCHO, colorDe, css, TOPE, type Capa } from "@/lib/geo";
import type { Contorno, DatosMapa, Departamento } from "@/lib/tipos";

// La vista 3D pesa bastante: solo se descarga si alguien la pide.
const Mapa3D = dynamic(() => import("@/componentes/Mapa3D"), {
  ssr: false,
  loading: () => <p className="apagado mapa-cargando">Cargando la vista 3D…</p>,
});

const CAPAS: Record<Capa, { titulo: string; pregunta: string; menos: string; mas: string; sinDato: string }> = {
  precio: {
    titulo: "Precios",
    pregunta: "¿Dónde está más cara la comida que hace un año?",
    menos: "más barata", mas: "más cara",
    sinDato: "sin central mayorista en la base",
  },
  lluvia: {
    titulo: "Lluvia",
    pregunta: "¿Dónde llovió más o menos de lo normal?",
    menos: "llovió menos", mas: "llovió más",
    sinDato: "sin sensores en la base",
  },
};

const MILISEGUNDOS_POR_MES = 900;

function valorDe(d: Departamento, capa: Capa, i: number): number | null {
  return d[capa]?.[i] ?? null;
}

function frase(d: Departamento, capa: Capa, i: number): string {
  const v = valorDe(d, capa, i);
  if (v === null) return CAPAS[capa].sinDato;
  if (capa === "precio") {
    return `Los alimentos están ${porcentaje(v)} frente al mismo mes del año pasado (valor típico de sus productos).`;
  }
  const mm = d.lluvia_mm?.[i];
  return `Llovió ${porcentaje(v)} frente a lo normal de ese mes${mm != null ? ` (${mm} mm medidos)` : ""}.`;
}

interface Props {
  datos: DatosMapa;
  contornos: Contorno[];
  /** Las estaciones del IDEAM ya ubicadas en el dibujo. */
  estaciones: [number, number][];
}

export function MapaAnimado({ datos, contornos, estaciones }: Props) {
  const ultimo = datos.periodos.length - 1;
  const [capa, setCapa] = useState<Capa>("precio");
  const [mes, setMes] = useState(ultimo);
  const [reproduciendo, setReproduciendo] = useState(false);
  const [elegido, setElegido] = useState<string | null>(null);
  const [vista, setVista] = useState<"2d" | "3d">("2d");

  const porCodigo = useMemo(() => new Map(datos.departamentos.map((d) => [d.codigo, d])), [datos.departamentos]);

  // La pelicula: avanza un mes cada cierto tiempo y se detiene al llegar al ultimo.
  useEffect(() => {
    if (!reproduciendo) return;
    const reloj = setInterval(() => {
      setMes((actual) => {
        if (actual >= ultimo) { setReproduciendo(false); return actual; }
        return actual + 1;
      });
    }, MILISEGUNDOS_POR_MES);
    return () => clearInterval(reloj);
  }, [reproduciendo, ultimo]);

  function alternarPelicula() {
    if (!reproduciendo && mes >= ultimo) setMes(0);      // si ya termino, arranca de nuevo
    setReproduciendo(!reproduciendo);
  }

  const texto = CAPAS[capa];
  const conDato = datos.departamentos.filter((d) => d[capa] !== null);
  const destacado = elegido ? porCodigo.get(elegido) : undefined;
  // Los que mas se alejan de cero este mes, para leer el mapa sin tener que adivinar.
  const extremos = [...conDato]
    .filter((d) => valorDe(d, capa, mes) !== null)
    .sort((a, b) => Math.abs(valorDe(b, capa, mes) as number) - Math.abs(valorDe(a, capa, mes) as number))
    .slice(0, 5);

  return (
    <section className="mapa-bloque" aria-labelledby="titulo-mapa">
      <div className="mapa-cabecera">
        <div>
          <h2 id="titulo-mapa">{texto.pregunta}</h2>
          <p className="nota">
            {capa === "precio"
              ? "Cada departamento se pinta con el cambio de precio de sus alimentos frente al mismo mes del año pasado."
              : "Cada departamento se pinta con la lluvia que midieron los sensores del IDEAM frente a lo normal de ese mes. Cada punto es una estación."}
          </p>
        </div>
        <div className="conmutadores">
          <div className="conmutador" role="group" aria-label="Qué mostrar">
            {(Object.keys(CAPAS) as Capa[]).map((c) => (
              <button key={c} type="button" aria-pressed={capa === c} onClick={() => setCapa(c)}>
                {c === "precio" ? <Tag size={15} aria-hidden="true" /> : <CloudRain size={15} aria-hidden="true" />}
                {CAPAS[c].titulo}
              </button>
            ))}
          </div>
          <div className="conmutador" role="group" aria-label="Tipo de vista">
            <button type="button" aria-pressed={vista === "2d"} onClick={() => setVista("2d")}><IconoMapa size={15} aria-hidden="true" />Plano</button>
            <button type="button" aria-pressed={vista === "3d"} onClick={() => setVista("3d")}><Box size={15} aria-hidden="true" />3D</button>
          </div>
        </div>
      </div>

      <div className="mapa-cuerpo">
        <div className="mapa-lienzo">
          {vista === "2d" ? (
            <svg viewBox={`0 0 ${ANCHO} ${ALTO}`} className="mapa" role="img"
              aria-label={`Mapa de Colombia: ${texto.titulo.toLowerCase()} en ${mesLargo(datos.periodos[mes])}`}>
              <defs>
                {/* Trama para "sin dato": se distingue del blanco aunque no se vean colores. */}
                <pattern id="trama" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
                  <rect width="6" height="6" fill="#efeae0" />
                  <line x1="0" y1="0" x2="0" y2="6" stroke="#d9d2c0" strokeWidth="2" />
                </pattern>
              </defs>
              {contornos.map((c, i) => {
                const d = porCodigo.get(c.codigo);
                const v = d ? valorDe(d, capa, mes) : null;
                return (
                  <path key={c.codigo} d={c.trazo} fillRule="evenodd"
                    className={`departamento${elegido === c.codigo ? " departamento-elegido" : ""}`}
                    style={{ fill: v === null ? "url(#trama)" : css(colorDe(v, capa)), animationDelay: `${i * 18}ms` }}
                    onClick={() => setElegido(elegido === c.codigo ? null : c.codigo)}>
                    <title>{d ? `${d.nombre}: ${v === null ? texto.sinDato : porcentaje(v)}` : c.codigo}</title>
                  </path>
                );
              })}
              {capa === "lluvia" && estaciones.map(([x, y], i) => (
                <circle key={i} className="estacion" cx={x} cy={y} r="1.6" style={{ animationDelay: `${(i % 60) * 12}ms` }} />
              ))}
            </svg>
          ) : (
            <Mapa3D departamentos={datos.departamentos} capa={capa} mes={mes} elegido={elegido} alElegir={setElegido} />
          )}

          <div className="escala" aria-hidden="true">
            <span>{texto.menos}</span>
            <span className={`escala-barra escala-${capa}`} />
            <span>{texto.mas}</span>
          </div>
          <p className="escala-nota">
            de −{TOPE[capa]} % a +{TOPE[capa]} % · <span className="muestra-sin-dato" /> {texto.sinDato}
          </p>
        </div>

        <div className="mapa-lectura">
          <div className="reproductor">
            <button type="button" className="boton-reproducir" onClick={alternarPelicula}>
              {reproduciendo ? <Pause size={16} aria-hidden="true" /> : <Play size={16} aria-hidden="true" />}
              {reproduciendo ? "Pausar" : "Ver los últimos 12 meses"}
            </button>
            <p className="mes-actual" aria-live="polite">{mesLargo(datos.periodos[mes])}</p>
            <input type="range" min={0} max={ultimo} value={mes} aria-label="Mes"
              onChange={(e) => { setReproduciendo(false); setMes(Number(e.target.value)); }} />
            <div className="reproductor-extremos"><span>{mesCorto(datos.periodos[0])}</span><span>{mesCorto(datos.periodos[ultimo])}</span></div>
          </div>

          {destacado ? (
            <div className="ficha" aria-live="polite">
              <h3>{destacado.nombre}</h3>
              <p>{frase(destacado, capa, mes)}</p>
              {destacado.estaciones > 0 && (
                <p className="nota">{destacado.estaciones} estaciones del IDEAM miden su clima.</p>
              )}
              <button type="button" className="enlace" onClick={() => setElegido(null)}>Ver todo el país</button>
            </div>
          ) : (
            <div className="ficha">
              <h3>Lo más marcado en {mesLargo(datos.periodos[mes])}</h3>
              <ol className="ranking">
                {extremos.map((d) => {
                  const v = valorDe(d, capa, mes) as number;
                  return (
                    <li key={d.codigo}>
                      <button type="button" className="enlace" onClick={() => setElegido(d.codigo)}>{d.nombre}</button>
                      <span className="barra-ranking" style={{
                        width: `${Math.min(Math.abs(v) / TOPE[capa], 1) * 100}%`, background: css(colorDe(v, capa)),
                      }} />
                      <span className="numero">{porcentaje(v)}</span>
                    </li>
                  );
                })}
              </ol>
              <p className="nota">Toca un departamento en el mapa para ver su dato.</p>
            </div>
          )}

          <p className="nota cobertura">
            <strong>Lo que este mapa no tiene.</strong> Hay dato de {texto.titulo.toLowerCase()} en{" "}
            {conDato.length} de {datos.departamentos.length} departamentos; los demás aparecen con trama
            porque {capa === "precio" ? "no tienen una central mayorista que reporte a SIPSA" : "todavía no descargamos sus sensores"}.
          </p>
        </div>
      </div>
    </section>
  );
}
