import type { NextConfig } from "next";

// La web es estatica: `next build` deja HTML, CSS y JS en la carpeta out/, que
// se puede publicar en cualquier servidor de archivos (Vercel, GitHub Pages).
// Los datos salen de public/datos/*.json, que escribe scripts/exportar_web.py.
//
// En GitHub Pages el sitio vive en una subcarpeta (/caso8-precios-agricolas):
// esa subcarpeta llega por la variable NEXT_PUBLIC_BASE_PATH. En local va vacia.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  basePath: process.env.NEXT_PUBLIC_BASE_PATH || undefined,
};

export default nextConfig;
