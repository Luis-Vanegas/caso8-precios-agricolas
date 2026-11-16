import type { NextConfig } from "next";

// La web es estatica: `next build` deja HTML, CSS y JS en la carpeta out/, que
// se puede publicar en cualquier servidor de archivos (Vercel, GitHub Pages).
// Los datos salen de public/datos/*.json, que escribe scripts/exportar_web.py.
const nextConfig: NextConfig = {
  output: "export",
};

export default nextConfig;
