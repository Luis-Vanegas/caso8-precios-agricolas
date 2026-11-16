"use client";

// Un numero que cuenta desde cero hasta su valor al aparecer. Si la persona
// pidio menos movimiento en su sistema, muestra el valor final de una vez.

import { useEffect, useState } from "react";

const DURACION = 900; // milisegundos

export function Contador({ valor }: { valor: number }) {
  const [mostrado, setMostrado] = useState(valor);

  useEffect(() => {
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    let cuadro = 0;
    const inicio = performance.now();
    const paso = (ahora: number) => {
      const avance = Math.min((ahora - inicio) / DURACION, 1);
      // Arranca rapido y frena al final, para que el numero "aterrice".
      setMostrado(Math.round(valor * (1 - Math.pow(1 - avance, 3))));
      if (avance < 1) cuadro = requestAnimationFrame(paso);
    };
    cuadro = requestAnimationFrame(paso);
    return () => cancelAnimationFrame(cuadro);
  }, [valor]);

  return <>{mostrado}</>;
}
