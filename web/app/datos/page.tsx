import type { Metadata } from "next";

import { Internacional } from "@/componentes/Internacional";
import type { DatosFuentes, DatosInternacional, Fuente } from "@/lib/tipos";
import datosCrudos from "@/public/datos/fuentes.json";
import internacionalCrudo from "@/public/datos/internacional.json";

export const metadata: Metadata = { title: "Los datos · Caso 8" };

const { fuentes, huecos } = datosCrudos as DatosFuentes;
const internacional = internacionalCrudo as DatosInternacional;
const REPO = "https://github.com/Luis-Vanegas/caso8-precios-agricolas/blob/main";
const enteros = new Intl.NumberFormat("es-CO");

const PASOS = [
  { titulo: "Traer", texto: "Un programa por fuente descarga solo lo nuevo. Los archivos crudos se guardan tal cual llegan y nunca se editan." },
  { titulo: "Limpiar", texto: "Se corrigen nombres, unidades y fechas, y todo se lleva a meses. Un mes sin dato se deja vacío: no se inventa." },
  { titulo: "Homologar", texto: "El DANE y la FAO llaman distinto a los mismos alimentos. Una tabla hecha a mano dice cuál es cuál y qué tan confiable es la equivalencia." },
  { titulo: "Unir", texto: "Todo entra a una sola base de 18 tablas, y 29 comprobaciones automáticas revisan que nada quedó mal cruzado." },
  { titulo: "Detectar", texto: "Sobre la base se calcula si un precio se movió de forma anormal, qué tiene que ver el clima y qué se espera." },
];

function Tarjeta({ fuente }: { fuente: Fuente }) {
  return (
    <article className="fuente">
      <p className="fuente-entidad">{fuente.entidad}</p>
      <h3>{fuente.nombre}</h3>
      <p>{fuente.aporta}</p>
      <dl className="fuente-datos">
        <div><dt>Se actualiza</dt><dd>{fuente.frecuencia}</dd></div>
        <div><dt>Último dato</dt><dd>{fuente.ultimo_dato}</dd></div>
        <div><dt>Registros</dt><dd className="numero">{enteros.format(fuente.filas)}</dd></div>
      </dl>
    </article>
  );
}

export default function LosDatos() {
  const nacionales = fuentes.filter((f) => f.origen === "nacional");
  const internacionales = fuentes.filter((f) => f.origen === "internacional");
  const total = fuentes.reduce((suma, f) => suma + f.filas, 0);

  const faltantes = [
    { cifra: `${huecos.departamentos_con_precio} de ${huecos.departamentos}`, texto: "departamentos tienen una central mayorista que reporta precios. Los demás no aparecen en el mapa de precios." },
    { cifra: `${huecos.departamentos_con_sensor} de ${huecos.departamentos}`, texto: "departamentos tienen sus sensores de lluvia descargados: son las zonas productoras que analiza el proyecto." },
    { cifra: `${huecos.meses_sin_precio} meses`, texto: "sin precios, de enero de 2021 a enero de 2022: el DANE no los publica en su servicio. El hueco se deja vacío." },
    { cifra: `${huecos.productos_con_zona} de ${huecos.productos}`, texto: "productos tienen identificada su zona de cultivo. Solo en esos se puede cruzar el precio con la lluvia." },
    { cifra: `${huecos.productos_comparables_fao} de ${huecos.productos}`, texto: "productos se pueden comparar con la FAO uno a uno. En el resto la FAO mezcla varios alimentos en un solo código." },
    { cifra: `${huecos.pronosticos_confiables} de ${huecos.productos}`, texto: "pronósticos a un mes aciertan más que suponer que el precio sigue igual. En los demás se avisa que la confianza es baja." },
    { cifra: `${huecos.relaciones_clima_firmes} de ${huecos.relaciones_clima}`, texto: "relaciones entre clima y precio se sostienen al revisarlas con rigor. Las demás pueden ser casualidad y no se presentan como hallazgo." },
    { cifra: huecos.ultimo_abastecimiento, texto: `es el último mes con toneladas de abastecimiento; los precios llegan hasta ${huecos.ultimo_precio}.` },
  ];

  return (
    <main className="pagina">
      <header className="cabecera">
        <p className="antetitulo">Los datos y cómo se hizo</p>
        <h1>De dónde sale cada número</h1>
        <p className="bajada">
          {fuentes.length} fuentes públicas y {enteros.format(total)} registros, unidos en una sola base.
          Unas miden desde Colombia y otras son de organismos internacionales: aquí van separadas.
        </p>
      </header>

      <section className="origenes" aria-label="Fuentes de datos">
        <div className="origen origen-nacional">
          <h2>Medido en Colombia</h2>
          <p className="nota">Entidades colombianas que toman el dato en el país: en la plaza y en la estación.</p>
          <div className="fuentes">{nacionales.map((f) => <Tarjeta key={f.nombre} fuente={f} />)}</div>
        </div>
        <div className="origen origen-internacional">
          <h2>De organismos internacionales</h2>
          <p className="nota">Publican datos de todo el mundo; de ellos se toma lo que corresponde a Colombia.</p>
          <div className="fuentes">{internacionales.map((f) => <Tarjeta key={f.nombre} fuente={f} />)}</div>
        </div>
      </section>

      <Internacional datos={internacional} />

      <section className="seccion" aria-labelledby="titulo-pasos">
        <h2 id="titulo-pasos">Cómo se hizo, en cinco pasos</h2>
        <ol className="pasos pasos-ancho">
          {PASOS.map((p, i) => (
            <li key={p.titulo} style={{ animationDelay: `${i * 90}ms` }}>
              <span className="paso-numero">{i + 1}</span>
              <strong>{p.titulo}</strong>
              <span>{p.texto}</span>
            </li>
          ))}
        </ol>
        <p className="nota">
          El detalle está en el repositorio:{" "}
          <a href={`${REPO}/notebooks/calculos_paso_a_paso.ipynb`}>los cálculos paso a paso</a> y{" "}
          <a href={`${REPO}/docs/diccionario_datos.md`}>el diccionario de las 18 tablas</a>.
        </p>
      </section>

      <section className="seccion" aria-labelledby="titulo-faltantes">
        <h2 id="titulo-faltantes">Lo que falta y lo que no se puede afirmar</h2>
        <p className="nota">Cada cifra se mide sobre la base; ninguna es una estimación.</p>
        <ul className="faltantes">
          {faltantes.map((f) => (
            <li key={f.texto}>
              <span className="faltante-cifra">{f.cifra}</span>
              <span>{f.texto}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className="seccion" aria-labelledby="titulo-referentes">
        <h2 id="titulo-referentes">En qué nos fijamos</h2>
        <p className="nota">Herramientas reales que ya vigilan precios de alimentos. Tomamos ideas, no datos.</p>
        <ul className="faltantes">
          <li>
            <span className="faltante-cifra"><a href="https://www.fao.org/giews/food-prices/price-tool/es/">FAO · FPMA</a></span>
            <span>Vigila precios de más de 90 países y cuenta cuándo un precio es anómalo frente a su propia historia. Es la idea detrás de nuestro semáforo.</span>
          </li>
          <li>
            <span className="faltante-cifra"><a href="https://dataviz.vam.wfp.org/economic_explorer/prices">PMA · Economic Explorer</a></span>
            <span>Muestra un alimento en un mercado mes a mes. Es la idea detrás de «La historia de un alimento».</span>
          </li>
          <li>
            <span className="faltante-cifra"><a href="https://www.dane.gov.co/index.php/estadisticas-por-tema/economia/precios-y-costos/sistema-de-informacion-de-precios-y-abastecimiento-del-sector-agropecuario-sipsa">DANE · SIPSA</a></span>
            <span>Nuestra fuente principal. Sus boletines comparan con el mismo periodo del año anterior, como hace el tablero.</span>
          </li>
        </ul>
        <p className="nota">Lo que agregamos: pronóstico puesto a prueba, meses más baratos, clima por zona de cultivo y lo internacional cruzado con lo nacional.</p>
      </section>
    </main>
  );
}
