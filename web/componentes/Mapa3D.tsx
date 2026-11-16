"use client";

// Vista 3D del mapa: cada departamento se levanta segun que tan lejos esta de lo
// normal. La altura dice "cuanto" y el color dice "hacia donde". Usa deck.gl.

import { GeoJsonLayer } from "@deck.gl/layers";
import DeckGL from "@deck.gl/react";
import { useEffect, useMemo, useState } from "react";

import { porcentaje } from "@/lib/formato";
import { colorDe, type Capa } from "@/lib/geo";
import type { Departamento } from "@/lib/tipos";

interface Rasgo {
  type: "Feature";
  properties: { codigo: string };
  geometry: { type: "MultiPolygon"; coordinates: number[][][][] };
}

const VISTA_INICIAL = { longitude: -73.4, latitude: 4.3, zoom: 4.55, pitch: 48, bearing: -12 };
const METROS_POR_PUNTO = 2200;      // altura de la columna por cada punto porcentual
const ALTURA_SIN_DATO = 3000;       // los que no tienen dato quedan casi planos

// La web puede vivir en una subcarpeta (GitHub Pages): los datos se piden desde ahi.
const BASE = process.env.NEXT_PUBLIC_BASE_PATH ?? "";

interface Props {
  departamentos: Departamento[];
  capa: Capa;
  mes: number;
  elegido: string | null;
  alElegir: (codigo: string | null) => void;
}

export default function Mapa3D({ departamentos, capa, mes, elegido, alElegir }: Props) {
  const [rasgos, setRasgos] = useState<Rasgo[] | null>(null);
  const [fallo, setFallo] = useState(false);

  useEffect(() => {
    fetch(`${BASE}/datos/colombia.json`)
      .then((r) => r.json())
      .then((g: { features: Rasgo[] }) => setRasgos(g.features.filter((f) => f.properties.codigo !== "88")))
      .catch(() => setFallo(true));
  }, []);

  const porCodigo = useMemo(() => new Map(departamentos.map((d) => [d.codigo, d])), [departamentos]);
  const valor = (f: Rasgo) => porCodigo.get(f.properties.codigo)?.[capa]?.[mes] ?? null;

  if (fallo) return <p className="apagado mapa-cargando">No se pudo cargar la vista 3D. La vista plana sigue disponible.</p>;
  if (!rasgos) return <p className="apagado mapa-cargando">Cargando la vista 3D…</p>;

  const capaDepartamentos = new GeoJsonLayer<Rasgo["properties"]>({
    id: "departamentos",
    data: rasgos,
    extruded: true,
    // Sin malla: con ella cada vertice del contorno dibuja una raya en la pared.
    wireframe: false,
    pickable: true,
    getElevation: (f) => {
      const v = valor(f as unknown as Rasgo);
      return v === null ? ALTURA_SIN_DATO : ALTURA_SIN_DATO + Math.abs(v) * METROS_POR_PUNTO;
    },
    getFillColor: (f) => {
      const [r, g, b] = colorDe(valor(f as unknown as Rasgo), capa);
      return [r, g, b, (f as unknown as Rasgo).properties.codigo === elegido ? 255 : 235];
    },
    getLineColor: [28, 37, 33, 90],
    // Al cambiar de mes o de capa, las columnas suben y bajan en vez de saltar.
    transitions: { getElevation: 700, getFillColor: 700 },
    updateTriggers: { getElevation: [capa, mes], getFillColor: [capa, mes, elegido] },
    onClick: (info) => alElegir((info.object as unknown as Rasgo | undefined)?.properties.codigo ?? null),
  });

  return (
    <div className="mapa-3d">
      <DeckGL
        initialViewState={VISTA_INICIAL}
        controller={{ scrollZoom: false, dragRotate: true }}
        layers={[capaDepartamentos]}
        getTooltip={({ object }) => {
          const f = object as unknown as Rasgo | undefined;
          if (!f) return null;
          const d = porCodigo.get(f.properties.codigo);
          const v = valor(f);
          return d ? `${d.nombre}: ${v === null ? "sin dato" : porcentaje(v)}` : null;
        }}
      />
      <p className="mapa-3d-ayuda">Arrastra para mover · clic derecho o Ctrl + arrastrar para girar</p>
    </div>
  );
}
