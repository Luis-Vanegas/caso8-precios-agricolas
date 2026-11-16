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
