# tests/ — pruebas automáticas

Correrlas: `.venv\Scripts\python.exe -m pytest tests -q` (deben salir solo puntos y "passed").

- Un archivo `test_<tema>.py` por parte del pipeline: adquisición, limpieza, integración, indicadores, etc.
- `test_app.py`: abre cada página de la app sin navegador; si no existe la base, se salta.
- `fixtures/`: recortes de respuestas reales de las fuentes.

Regla: **ninguna prueba usa internet**; trabajan sobre las fixtures.
Qué NO hacer: no editar las fixtures a mano para que una prueba pase.

Siguiente paso: [src/LEEME.md](../src/LEEME.md) explica qué módulo prueba cada archivo.
