import type { Metadata } from "next";
import { Fraunces, Inter, JetBrains_Mono } from "next/font/google";
import "./globals.css";
import "./modulos.css";
import "./clima.css";

import { Navegacion } from "@/componentes/Navegacion";

// Las tres familias del DESIGN.md: Fraunces da la voz en los titulos, Inter es
// el texto y JetBrains Mono los numeros (los digitos tienen todos el mismo ancho).
const titulos = Fraunces({ subsets: ["latin"], weight: ["500", "700"], variable: "--fuente-titulos" });
const texto = Inter({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--fuente-texto" });
const numeros = JetBrains_Mono({ subsets: ["latin"], weight: ["500"], variable: "--fuente-numeros" });

export const metadata: Metadata = {
  title: "Precios de la plaza · Caso 8",
  description:
    "Qué alimentos subieron, cuáles bajaron y qué se espera: precios mayoristas de Colombia con semáforo y pronóstico.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${titulos.variable} ${texto.variable} ${numeros.variable}`}>
      <body>
        {/* La franja tricolor es la marca del proyecto (DESIGN.md): no es un dato. */}
        <div className="franja" aria-hidden="true" />
        <Navegacion />
        {children}
      </body>
    </html>
  );
}
