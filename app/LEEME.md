# app/ — la aplicación Streamlit

- `streamlit_app.py`: solo el menú de 7 páginas, que están en `paginas/`: inicio, canasta, mapa, clima, efecto_clima (¿Cuánto afecta el clima?), pronostico y como_lo_hicimos.
- `secciones/`: lo que antes eran páginas aparte (detalle de producto, clima hoy, El Niño, sensor IDEAM, la cadena, recorrido, calidad, comercio). Cada una es una función `mostrar()` que la página que la absorbió abre en una pestaña.
- `datos.py`: único lugar que abre la base `data/processed/caso8.duckdb`.
- `graficas.py` y `estilo.py`: gráficas y apariencia (colores, tipografía).
- `ejemplos/`: muestras reales pequeñas que se ven en la pestaña "Recorrido paso a paso" de "Cómo lo hicimos"; se regeneran con `scripts/generar_ejemplos.py`.

Abrirla: `.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py`.
Antes de correr `scripts/integrar.py` o `scripts/diario.py`, **cerrar la app**: tiene la base abierta y Windows bloquea la escritura.

Siguiente paso: las tablas que la app espera están descritas en [docs/contrato_datos.md](../docs/contrato_datos.md).
