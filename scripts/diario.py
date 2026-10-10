"""Corrida diaria completa: descarga lo nuevo, limpia e integra. Un solo comando.

Uso (con la app CERRADA: si esta abierta, Windows bloquea la base):
    python scripts/diario.py

Reglas:
- Si una fuente falla al descargar (actualizar.py devuelve 1), se sigue: la
  limpieza usa la ultima descarga buena de esa fuente. Se avisa al final.
- Si falla la limpieza o la integracion, se detiene: seguir dejaria la base a
  medio armar.
- Devuelve 0 si todo salio bien y 1 si algo fallo, para que el Programador de
  tareas de Windows lo marque.

Cada paso corre como un proceso aparte, igual que si se escribiera a mano.
"""

from __future__ import annotations

import subprocess
import sys
from datetime import datetime
from pathlib import Path

CARPETA = Path(__file__).resolve().parent

# (script, puede fallar sin detener la cadena)
PASOS = (
    ("actualizar.py", True),
    ("preparar.py", False),
    ("integrar.py", False),
)


def ejecutar_script(script: str) -> int:
    """Corre un script con el mismo Python (el del .venv) y devuelve su codigo de salida."""
    return subprocess.run([sys.executable, str(CARPETA / script)], cwd=CARPETA.parent).returncode


def correr(ejecutar=ejecutar_script) -> int:
    """Corre los pasos en orden. `ejecutar` se puede cambiar en las pruebas."""
    hubo_fallo = False
    for script, tolerante in PASOS:
        print(f"\n===== {datetime.now():%Y-%m-%d %H:%M} {script} =====", flush=True)
        codigo = ejecutar(script)
        if codigo == 0:
            continue
        hubo_fallo = True
        if tolerante:
            print(f"AVISO: {script} termino con errores; se sigue con la ultima descarga buena.")
        else:
            print(f"ERROR: {script} fallo; se detiene la corrida para no dejar la base a medio armar.")
            break
    print("\nResultado:", "con errores (revisar arriba)" if hubo_fallo else "todo bien")
    return 1 if hubo_fallo else 0


if __name__ == "__main__":
    sys.exit(correr())
