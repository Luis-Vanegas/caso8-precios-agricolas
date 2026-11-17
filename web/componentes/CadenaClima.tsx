// "¿El clima mueve los precios?": la cadena El Nino -> lluvia -> comida que llega
// -> precio, con cuanto se sostiene cada paso. Es la respuesta central del modulo.

import { ArrowRight, CloudRain, Tag, Thermometer, Truck } from "lucide-react";

import { mesLargo } from "@/lib/formato";
import type { DatosClima, Eslabon, Hallazgo } from "@/lib/tipos";

type Fuerza = "firme" | "parcial" | "nada";

/** Que tan bien se sostiene un eslabon, segun cuantas de sus pruebas pasan. */
function fuerza(e: Eslabon): Fuerza {
  const parte = e.pruebas ? e.firmes / e.pruebas : 0;
  if (parte >= 0.4) return "firme";
  return e.firmes > 0 ? "parcial" : "nada";
}

const VEREDICTO: Record<Fuerza, string> = {
  firme: "Se sostiene",
  parcial: "Solo en algunos casos",
  nada: "No se encontró",
};

const ICONO = { "El Niño": Thermometer, Lluvia: CloudRain, "Comida que llega": Truck, Precio: Tag } as const;

function meses(n: number): string {
  return n === 0 ? "el mismo mes" : n === 1 ? "un mes después" : `${n} meses después`;
}

/** Un hallazgo dicho en palabras, sin coeficientes. */
function enPalabras(clave: string, h: Hallazgo): string {
  const baja = (h.coeficiente ?? 0) < 0;
  switch (clave) {
    case "oni->lluvia":
      return `${h.departamento}: con El Niño llueve ${baja ? "menos" : "más"} (${meses(h.rezago_meses)})`;
    case "oferta->precio":
      return baja
        ? `${h.producto}: cuando llega más, el precio baja`
        : `${h.producto}: se mueve al revés de lo esperado`;
    case "lluvia->precio":
      return `${h.producto}: cuando llueve más en ${h.departamento}, el precio ${baja ? "baja" : "sube"} ${meses(h.rezago_meses)}`;
    default:
      return `${h.producto ?? h.departamento}`;
  }
}

function Paso({ e, posicion }: { e: Eslabon; posicion: number }) {
  const f = fuerza(e);
  const Desde = ICONO[e.desde as keyof typeof ICONO] ?? CloudRain;
  const Hasta = ICONO[e.hasta as keyof typeof ICONO] ?? Tag;
  const parte = e.pruebas ? (e.firmes / e.pruebas) * 100 : 0;
  return (
    <li className={`eslabon eslabon-${f}`} style={{ animationDelay: `${posicion * 110}ms` }}>
      <div className="eslabon-ruta" aria-hidden="true">
        <span className="nodo"><Desde size={22} strokeWidth={1.8} /></span>
        <span className="conector"><ArrowRight size={18} strokeWidth={2} /></span>
        <span className="nodo"><Hasta size={22} strokeWidth={1.8} /></span>
      </div>
      <p className="eslabon-nombres">{e.desde} → {e.hasta}</p>
      <h3>{e.pregunta}</h3>
      <p className="veredicto"><span className={`sello sello-${f}`}>{VEREDICTO[f]}</span></p>
      <div className="medidor" role="img" aria-label={`${e.firmes} de ${e.pruebas} pruebas se sostienen`}>
        <span className="medidor-lleno" style={{ width: `${parte}%` }} />
      </div>
      <p className="medidor-texto"><span className="numero">{e.firmes} de {e.pruebas}</span> pruebas se sostienen</p>
      {e.hallazgos.length > 0 && (
        <ul className="hallazgos">
          {e.hallazgos.slice(0, 4).map((h) => <li key={enPalabras(e.eslabon, h)}>{enPalabras(e.eslabon, h)}</li>)}
        </ul>
      )}
    </li>
  );
}

export function CadenaClima({ datos }: { datos: DatosClima }) {
  const [nino, lluviaOferta, ofertaPrecio, directo] = datos.cadena;
  const total = datos.cadena.reduce((s, e) => s + e.pruebas, 0);
  const firmes = datos.cadena.reduce((s, e) => s + e.firmes, 0);

  return (
    <section className="cadena" aria-labelledby="titulo-cadena">
      <p className="antetitulo">La pregunta de fondo</p>
      <h2 id="titulo-cadena">¿El clima mueve los precios?</h2>
      <p className="respuesta">
        <strong>Deja huella, pero débil y no en todo.</strong> El Niño sí cambia la lluvia. Lo que no
        logramos ver es que esa lluvia cambie cuánta comida llega a las plazas: ahí se corta la cadena.
        El precio responde con claridad en un solo producto, el {directo.hallazgos[0]?.producto?.toLowerCase() ?? "tomate"}.
      </p>

      <ol className="eslabones">
        {[nino, lluviaOferta, ofertaPrecio, directo].map((e, i) => <Paso key={e.eslabon} e={e} posicion={i} />)}
      </ol>

      <p className="nota">
        Se hicieron {total} pruebas y {firmes} se sostienen después de descontar la suerte (con tantas
        pruebas, algunas salen bien por casualidad). Además se revisó si los precios cambiaron de
        comportamiento al empezar El Niño o La Niña: {datos.quiebres.firmes} de {datos.quiebres.pruebas} casos.
        Que dos cosas se muevan juntas no prueba que una cause la otra.
      </p>

      {datos.pistas.length > 0 && (
        <div className="pistas">
          <h3>Lo que la lluvia pasada sugiere para {mesLargo(datos.proximo_mes)}</h3>
          <ul>
            {datos.pistas.map((p) => (
              <li key={p.producto + p.departamento}>
                <span className="pista-producto">{p.producto}</span>
                <span className={`pista-senal pista-${p.senal === "al alza" ? "sube" : p.senal === "a la baja" ? "baja" : "nada"}`}>
                  {p.senal === "sin dato" ? "sin señal" : `podría ir ${p.senal}`}
                </span>
                <span className="pista-porque">
                  En {mesLargo(p.mes_de_la_lluvia)} llovió {p.llovio_mas ? "más" : "menos"} de lo normal en {p.departamento},
                  y eso suele notarse en el precio {meses(p.rezago_meses)}.
                </span>
                <span className="pista-acierto">
                  En el pasado esta pista acertó la dirección <strong>{p.aciertos} de {p.meses}</strong> veces
                  ({Math.round((p.aciertos / p.meses) * 100)} %). Tirar una moneda acierta la mitad.
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
