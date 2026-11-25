// Como se escriben los numeros y las fechas en pantalla, y como se lee el semaforo.

import type { Estado, Fila } from "./tipos";

const MESES_CORTOS = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
  "septiembre", "octubre", "noviembre", "diciembre"];

const enteros = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 0 });
const un_decimal = new Intl.NumberFormat("es-CO", { minimumFractionDigits: 1, maximumFractionDigits: 1 });

/** 6193 -> "$6.193" */
export function pesos(valor: number | null): string {
  return valor === null ? "sin dato" : `$${enteros.format(valor)}`;
}

/** 18.04 -> "+18,0 %"; -3.2 -> "−3,2 %" */
export function porcentaje(valor: number | null): string {
  if (valor === null) return "sin dato";
  const signo = valor > 0 ? "+" : valor < 0 ? "−" : "";
  return `${signo}${un_decimal.format(Math.abs(valor))} %`;
}

/** 202609 -> "sep 2026" */
export function mesCorto(periodo: number): string {
  return `${MESES_CORTOS[(periodo % 100) - 1]} ${Math.floor(periodo / 100)}`;
}

/** 202609 -> "septiembre de 2026" */
export function mesLargo(periodo: number): string {
  return `${MESES[(periodo % 100) - 1]} de ${Math.floor(periodo / 100)}`;
}

/** Un cambio de menos de 1 % se muestra como "igual": es ruido, no una subida. */
export const CAMBIO_MINIMO = 1;

export type Direccion = "sube" | "baja" | "igual" | "sin dato";

export function direccion(cambio: number | null): Direccion {
  if (cambio === null) return "sin dato";
  if (Math.abs(cambio) < CAMBIO_MINIMO) return "igual";
  return cambio > 0 ? "sube" : "baja";
}


const GRAVEDAD: Record<Estado, number> = { "sin dato": 0, verde: 1, amarilla: 2, roja: 3 };

/** El estado de un producto es el peor de sus dos semaforos (mes y anio). */
export function estadoGeneral(fila: Fila): Estado {
  return GRAVEDAD[fila.estado_anio] > GRAVEDAD[fila.estado_mes] ? fila.estado_anio : fila.estado_mes;
}

export const NOMBRE_ESTADO: Record<Estado, string> = {
  verde: "Normal",
  amarilla: "Atención",
  roja: "Anormal",
  "sin dato": "Sin historia",
};

/** Explica en palabras por que un producto esta en atencion o anormal. */
export function motivoEstado(fila: Fila): string {
  const estado = estadoGeneral(fila);
  if (estado === "sin dato") return "Aún no hay meses suficientes para comparar";
  if (estado === "verde") return "Se mueve como suele moverse";
  const porAnio = GRAVEDAD[fila.estado_anio] >= GRAVEDAD[fila.estado_mes];
  const cambio = porAnio ? fila.cambio_anio_pct : fila.cambio_mes_pct;
  const sentido = (cambio ?? 0) > 0 ? "Subió" : "Bajó";
  return `${sentido} más de lo habitual frente al ${porAnio ? "año pasado" : "mes pasado"}`;
}

/** Que tan lejos de lo normal esta: sirve para poner primero lo mas urgente. */
export function urgencia(fila: Fila): number {
  return Math.max(Math.abs(fila.z_mes ?? 0), Math.abs(fila.z_anio ?? 0));
}

/** Mas de este % por encima o por debajo del precio tipico = caro o barato. Es una convencion de lectura. */
export const UMBRAL_CARO = 10;

export type Nivel = "barato" | "normal" | "caro" | "sin dato";

/**
 * Compara el precio de hoy con su precio tipico: la mediana de los 12 meses anteriores con dato.
 * La mediana no se deja arrastrar por un mes raro. Pide al menos 6 meses para opinar.
 */
export function nivelPrecio(fila: Fila): { nivel: Nivel; frente_tipico: number | null; tipico: number | null } {
  const iHoy = fila.serie.findLastIndex((v) => v !== null);
  const hoy = iHoy >= 0 ? fila.serie[iHoy] : null;
  const previos = fila.serie.slice(Math.max(0, iHoy - 12), Math.max(0, iHoy))
    .filter((v): v is number => v !== null)
    .sort((a, b) => a - b);
  if (hoy === null || previos.length < 6) return { nivel: "sin dato", frente_tipico: null, tipico: null };
  const m = Math.floor(previos.length / 2);
  const tipico = previos.length % 2 ? previos[m] : (previos[m - 1] + previos[m]) / 2;
  const frente_tipico = (hoy / tipico - 1) * 100;
  const nivel = frente_tipico > UMBRAL_CARO ? "caro" : frente_tipico < -UMBRAL_CARO ? "barato" : "normal";
  return { nivel, frente_tipico, tipico };
}

export const NOMBRE_NIVEL: Record<Nivel, string> = {
  barato: "Barato", normal: "Normal", caro: "Caro", "sin dato": "Sin historia",
};

/** Cambio esperado, en %, entre el precio de hoy y el pronostico del proximo mes. */
export function cambioEsperado(fila: Fila): number | null {
  const proximo = fila.pronostico?.meses[0]?.valor ?? null;
  if (proximo === null || fila.precio === null || fila.precio === 0) return null;
  return (proximo / fila.precio - 1) * 100;
}
