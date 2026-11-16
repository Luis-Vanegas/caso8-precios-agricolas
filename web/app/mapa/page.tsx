import type { Metadata } from "next";

import { CadenaClima } from "@/componentes/CadenaClima";
import { ComoMideElSensor, ElNino, LluviaEsperada } from "@/componentes/Clima";
import { MapaAnimado } from "@/componentes/MapaAnimado";
import { contornos, crearProyeccion } from "@/lib/geo";
import type { DatosClima, DatosMapa } from "@/lib/tipos";
import climaCrudo from "@/public/datos/clima.json";
import colombia from "@/public/datos/colombia.json";
import datosCrudos from "@/public/datos/mapa.json";

export const metadata: Metadata = { title: "Mapa y clima · Caso 8" };

const datos = datosCrudos as unknown as DatosMapa;
const clima = climaCrudo as DatosClima;

// El contorno de cada departamento se calcula una sola vez, al construir el sitio.
const proyectar = crearProyeccion(colombia.features);
const dibujo = contornos(colombia.features, proyectar);
const estaciones = datos.estaciones.map(([lon, lat]) => proyectar(lon, lat));

export default function MapaYClima() {
  const conSensor = datos.departamentos.filter((d) => d.estaciones > 0).length;
  return (
    <main className="pagina">
      <header className="cabecera">
        <p className="antetitulo">Dónde y por qué</p>
        <h1>El mapa de los precios y del clima</h1>
        <p className="bajada">
          Dónde está más cara la comida, dónde llovió más o menos de lo normal, y qué dice el clima sobre
          los próximos meses. El clima es una pista, no una causa probada.
        </p>
      </header>

      <MapaAnimado datos={datos} contornos={dibujo} estaciones={estaciones} />

      <CadenaClima datos={clima} />

      <section className="clima" aria-labelledby="titulo-clima">
        <h2 id="titulo-clima">El clima hoy y cómo lo medimos</h2>
        <div className="clima-rejilla">
          <ElNino nino={datos.nino} />
          <ComoMideElSensor estaciones={datos.estaciones.length} departamentos={conSensor} />
        </div>
        <LluviaEsperada departamentos={datos.departamentos} />
      </section>
    </main>
  );
}
