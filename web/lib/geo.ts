// Convierte longitud y latitud en posiciones de dibujo, y valores en colores.
// Se hace a mano (sin libreria de mapas): Colombia esta cerca del ecuador y
// una proyeccion sencilla la dibuja sin deformarla.

import type { Contorno } from "./tipos";

interface Rasgo {
  properties: { codigo: string };
  geometry: { coordinates: number[][][][] }; // MultiPolygon: poligonos > anillos > puntos
}

export const ANCHO = 520;
export const ALTO = 640;
const MARGEN = 12;

// San Andres esta a 700 km de la costa: si entra al encuadre, el pais se ve diminuto.
const FUERA_DEL_ENCUADRE = new Set(["88"]);

export interface Proyeccion {
  (lon: number, lat: number): [number, number];
}

/** Arma la funcion que ubica cualquier punto del pais dentro del dibujo. */
export function crearProyeccion(rasgos: Rasgo[]): Proyeccion {
  let lonMin = Infinity, lonMax = -Infinity, latMin = Infinity, latMax = -Infinity;
  for (const r of rasgos) {
    if (FUERA_DEL_ENCUADRE.has(r.properties.codigo)) continue;
    for (const poligono of r.geometry.coordinates) for (const anillo of poligono) for (const [lon, lat] of anillo) {
      lonMin = Math.min(lonMin, lon); lonMax = Math.max(lonMax, lon);
      latMin = Math.min(latMin, lat); latMax = Math.max(latMax, lat);
    }
  }
  // Un grado de longitud mide menos que uno de latitud lejos del ecuador: se corrige con el coseno.
  const k = Math.cos((((latMin + latMax) / 2) * Math.PI) / 180);
  const escala = Math.min((ANCHO - 2 * MARGEN) / ((lonMax - lonMin) * k), (ALTO - 2 * MARGEN) / (latMax - latMin));
  const sobraX = (ANCHO - (lonMax - lonMin) * k * escala) / 2;
  const sobraY = (ALTO - (latMax - latMin) * escala) / 2;
  return (lon, lat) => [sobraX + (lon - lonMin) * k * escala, sobraY + (latMax - lat) * escala];
}

/** El contorno de cada departamento como trazo SVG. */
export function contornos(rasgos: Rasgo[], proyectar: Proyeccion): Contorno[] {
  return rasgos
    .filter((r) => !FUERA_DEL_ENCUADRE.has(r.properties.codigo))
    .map((r) => {
      let trazo = "";
      let sumaX = 0, sumaY = 0, n = 0;
      for (const poligono of r.geometry.coordinates) {
        for (const anillo of poligono) {
          anillo.forEach(([lon, lat], i) => {
            const [x, y] = proyectar(lon, lat);
            trazo += `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`;
            sumaX += x; sumaY += y; n += 1;
          });
          trazo += "Z";
        }
      }
      return { codigo: r.properties.codigo, trazo, centro: [sumaX / n, sumaY / n] as [number, number] };
    });
}

// --- Colores ------------------------------------------------------------------------

type RGB = [number, number, number];
const BLANCO: RGB = [255, 255, 255];
export const ROJO: RGB = [192, 57, 43];
export const AZUL: RGB = [29, 78, 137];
export const TIERRA: RGB = [138, 90, 43];
export const SIN_DATO: RGB = [230, 224, 210];

function mezclar(a: RGB, b: RGB, t: number): RGB {
  return [0, 1, 2].map((i) => Math.round(a[i] + (b[i] - a[i]) * t)) as RGB;
}

export type Capa = "precio" | "lluvia";

/** Hasta donde llega la escala: mas alla de este valor el color ya no cambia. */
export const TOPE: Record<Capa, number> = { precio: 40, lluvia: 60 };

/**
 * Color de un valor en una escala que parte de blanco en cero.
 * Precio: azul = mas barato que hace un anio, rojo = mas caro.
 * Lluvia: cafe = llovio menos de lo normal, azul = llovio mas.
 */
export function colorDe(valor: number | null, capa: Capa): RGB {
  if (valor === null) return SIN_DATO;
  const t = Math.min(Math.abs(valor) / TOPE[capa], 1);
  const [negativo, positivo] = capa === "precio" ? [AZUL, ROJO] : [TIERRA, AZUL];
  return mezclar(BLANCO, valor < 0 ? negativo : positivo, 0.12 + 0.88 * t);
}

export const css = ([r, g, b]: RGB) => `rgb(${r} ${g} ${b})`;
