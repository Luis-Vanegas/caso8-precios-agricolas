"use client";

// El menu de los tres modulos. Marca en cual esta la persona.

import Link from "next/link";
import { usePathname } from "next/navigation";

const MODULOS = [
  { ruta: "/", titulo: "Precios", detalle: "qué subió y qué viene" },
  { ruta: "/mapa", titulo: "Mapa y clima", detalle: "dónde y por qué" },
  { ruta: "/datos", titulo: "Los datos", detalle: "de dónde sale todo" },
];

export function Navegacion() {
  // Con la exportacion estatica las rutas terminan en "/": se compara sin esa barra final.
  const actual = usePathname().replace(/\/$/, "") || "/";
  return (
    <header className="barra">
      <div className="barra-interior">
        <Link href="/" className="marca">Precios de la plaza</Link>
        <nav aria-label="Módulos">
          {MODULOS.map((m) => (
            <Link key={m.ruta} href={m.ruta} className="modulo" aria-current={actual === m.ruta ? "page" : undefined}>
              <span className="modulo-titulo">{m.titulo}</span>
              <span className="modulo-detalle">{m.detalle}</span>
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}
