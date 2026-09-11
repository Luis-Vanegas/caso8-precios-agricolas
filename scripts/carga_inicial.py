"""Carga inicial: baja todo desde cero, ignorando lo ya registrado.

Es `actualizar.py --forzar`. No se duplica la logica: se reutiliza.

Uso:
    python scripts/carga_inicial.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.actualizar import main as actualizar

if __name__ == "__main__":
    sys.exit(actualizar(["--forzar"]))
