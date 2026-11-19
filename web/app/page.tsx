import { ArrowDownRight, ArrowUpRight } from "lucide-react";

import { HistoriaAlimento } from "@/componentes/HistoriaAlimento";
import { PronosticoHonesto } from "@/componentes/PronosticoHonesto";
import { Tablero } from "@/componentes/Tablero";
import type { DatosHistoria, Tablero as DatosTablero } from "@/lib/tipos";
import historiaCruda from "@/public/datos/historia.json";
import datosCrudos from "@/public/datos/tablero.json";

// El JSON lo escribe scripts/exportar_web.py; aqui solo se le pone el tipo.
const datos = datosCrudos as DatosTablero;
const historia = historiaCruda as DatosHistoria;
const nacionales = datos.filas.filter((f) => f.mercado === "Nacional");

export default function Inicio() {
  return (
    <main className="pagina">
      <header className="cabecera">
        <p className="antetitulo">Precios de la plaza · {datos.ultimo_mes_texto}</p>
        <h1>¿Qué alimentos subieron, cuáles bajaron y qué viene?</h1>
        <p className="bajada">
          Precio mayorista de {new Set(datos.filas.map((f) => f.producto)).size} alimentos en{" "}
          {datos.mercados.length - 1} ciudades de Colombia, comparado con el mes pasado y con el mismo mes
          del año pasado, y lo que se espera para los próximos tres meses.
        </p>
      </header>

      <Tablero datos={datos} />

      <section className="leyenda" aria-labelledby="titulo-leyenda">
        <h2 id="titulo-leyenda">Cómo leer esta tabla</h2>
        <dl>
          <div>
            <dt className="con-icono"><span className="icono-direccion icono-sube" aria-hidden="true"><ArrowUpRight size={15} strokeWidth={2.4} /></span> sube · <span className="icono-direccion icono-baja" aria-hidden="true"><ArrowDownRight size={15} strokeWidth={2.4} /></span> baja</dt>
            <dd>La dirección del precio. Rojo es que subió, azul que bajó. Un cambio de menos de 1 % se muestra como «=».</dd>
          </div>
          <div>
            <dt>Frente a hace un año</dt>
            <dd>Compara con el mismo mes del año pasado. Así no se confunde una subida real con la temporada: en cosecha todo baja.</dd>
          </div>
          <div>
            <dt>
              <span className="pastilla pastilla-verde">Normal</span>{" "}
              <span className="pastilla pastilla-amarilla">Atención</span>{" "}
              <span className="pastilla pastilla-roja">Anormal</span>
            </dt>
            <dd>
              Dice si el movimiento es raro <em>para ese producto</em>. Un limón que sube 30 % puede ser normal,
              porque siempre se mueve mucho; un banano que sube 30 % no lo es.
            </dd>
          </div>
          <div>
            <dt>Confianza</dt>
            <dd>
              «Alta» solo cuando el pronóstico acertó más, en los últimos dos años, que suponer que el precio
              seguía igual. Con «Baja», el pronóstico es una referencia y nada más.
            </dd>
          </div>
        </dl>
        <p className="nota">
          Fuente de los precios: SIPSA (DANE). Datos hasta {datos.ultimo_mes_texto}; el mes en curso no se
          incluye porque todavía le faltan días. Los umbrales del estado son una convención de este
          proyecto, no una norma oficial.
        </p>
      </section>

      <HistoriaAlimento historia={historia} nacionales={nacionales} />

      <PronosticoHonesto nacionales={nacionales} />
    </main>
  );
}
