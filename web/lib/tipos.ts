// La forma del archivo public/datos/tablero.json, que escribe scripts/exportar_web.py.

/** Estado del semaforo. "sin dato" = no hay historia suficiente para decir si es raro. */
export type Estado = "verde" | "amarilla" | "roja" | "sin dato";

export interface MesPronosticado {
  periodo: number; // AAAAMM
  valor: number | null;
  minimo: number | null;
  maximo: number | null;
  /** "regresion" (usa clima), "estacional" (repite el anio pasado) o "sin_cambio". */
  metodo: string;
  confiable: boolean;
}

export interface Pronostico {
  meses: MesPronosticado[];
  /** Verdadero solo si el modelo se equivoca menos que suponer "sigue igual". */
  confiable: boolean;
  error_modelo_pct: number | null;
  error_ingenuo_pct: number | null;
}

export interface Fila {
  producto: string;
  mercado: string;
  /** Pesos por kilo en el ultimo mes cerrado. */
  precio: number | null;
  cambio_mes_pct: number | null;
  estado_mes: Estado;
  z_mes: number | null;
  cambio_anio_pct: number | null;
  estado_anio: Estado;
  z_anio: number | null;
  /** Un precio por cada mes de `periodos`; null donde no hay dato. */
  serie: (number | null)[];
  /** Solo la fila "Nacional" tiene pronostico. */
  pronostico: Pronostico | null;
}

export interface Tablero {
  ultimo_mes: number;
  ultimo_mes_texto: string;
  generado: string;
  periodos: number[];
  mercados: string[];
  umbrales: { amarilla: number; roja: number };
  filas: Fila[];
}

// --- public/datos/mapa.json ---------------------------------------------------------

export interface LluviaEsperada {
  periodo: number;
  /** Milimetros en el mes: escenario seco, central y lluvioso. */
  seco: number | null;
  central: number | null;
  lluvioso: number | null;
}

export interface Departamento {
  codigo: string; // codigo DANE, con el cero a la izquierda
  nombre: string;
  /** Cambio % del precio frente al mismo mes del anio pasado, un valor por mes. null = sin mercado. */
  precio: (number | null)[] | null;
  /** Lluvia medida por sensores frente a lo normal, en %. null = sin sensores en la base. */
  lluvia: (number | null)[] | null;
  lluvia_mm: (number | null)[] | null;
  estaciones: number;
  lluvia_esperada: LluviaEsperada[] | null;
}

export interface Nino {
  fase: string;
  anomalia: number | null;
  periodo: number;
  trimestre: string;
  provisional: boolean;
  serie: { periodo: number; anomalia: number | null }[];
}

export interface DatosMapa {
  periodos: number[];
  departamentos: Departamento[];
  estaciones: [number, number][]; // [longitud, latitud]
  nino: Nino;
}

/** Un departamento ya convertido a dibujo: su contorno como trazo SVG. */
export interface Contorno {
  codigo: string;
  trazo: string;
  /** Centro aproximado, para ubicar etiquetas. */
  centro: [number, number];
}

// --- public/datos/fuentes.json ------------------------------------------------------

export interface Fuente {
  nombre: string;
  entidad: string;
  origen: "nacional" | "internacional";
  aporta: string;
  frecuencia: string;
  tablas: string[];
  filas: number;
  ultimo_dato: string;
}

export interface Huecos {
  departamentos: number;
  departamentos_con_precio: number;
  departamentos_con_sensor: number;
  meses_sin_precio: number;
  productos: number;
  productos_con_zona: number;
  productos_comparables_fao: number;
  pronosticos_confiables: number;
  relaciones_clima: number;
  relaciones_clima_firmes: number;
  ultimo_precio: string;
  ultimo_abastecimiento: string;
}

export interface DatosFuentes {
  fuentes: Fuente[];
  huecos: Huecos;
}

// --- public/datos/clima.json --------------------------------------------------------

export interface Hallazgo {
  producto: string | null;
  departamento: string | null;
  rezago_meses: number;
  /** Negativo = cuando una sube, la otra baja. */
  coeficiente: number | null;
}

/** Un paso de la cadena El Nino -> lluvia -> comida que llega -> precio. */
export interface Eslabon {
  eslabon: string;
  desde: string;
  hasta: string;
  pregunta: string;
  /** Cuantas relaciones se probaron y cuantas se sostienen (q-valor menor a 0,1). */
  pruebas: number;
  firmes: number;
  hallazgos: Hallazgo[];
}

export interface Pista {
  producto: string;
  departamento: string;
  rezago_meses: number;
  mes_de_la_lluvia: number;
  llovio_mas: boolean | null;
  senal: "al alza" | "a la baja" | "sin dato";
  /** Cuantas veces esta pista acerto la direccion del precio en el pasado. */
  aciertos: number;
  meses: number;
}

export interface DatosClima {
  cadena: Eslabon[];
  pistas: Pista[];
  proximo_mes: number;
  quiebres: { pruebas: number; firmes: number };
}

// --- public/datos/historia.json ---------------------------------------------------------

export interface HistoriaProducto {
  producto: string;
  /** Precio nacional de cada mes de `periodos`; null donde no hay dato (el hueco de 2021). */
  serie: (number | null)[];
  /** Enero a diciembre: % por encima (+) o por debajo (−) del promedio del año. null = pocos años. */
  estacionalidad: (number | null)[];
  anios_estacionalidad: number;
}

export interface DatosHistoria {
  periodos: number[];
  productos: HistoriaProducto[];
}

// --- public/datos/internacional.json ----------------------------------------------------

export interface DatosInternacional {
  anio_fao: number;
  /** Nuestros productos: qué parte de lo que consume el país se importa. */
  dependencia_nuestros: { producto: string; item_fao: string; dependencia_pct: number | null }[];
  mas_importados: { item_fao: string; dependencia_pct: number | null; importacion_t: number | null }[];
  /** Índices base 100 = promedio de 2020. */
  indices: { periodos: number[]; comida: (number | null)[]; Urea?: (number | null)[]; DAP?: (number | null)[] };
}
