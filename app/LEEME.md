# app/ — la aplicación Streamlit

- `streamlit_app.py`: solo el menú; cada página está en `paginas/` (inicio, semáforo, producto, canasta, mapa, clima, cadena, calidad, recorrido, entre otras).
- `datos.py`: único lugar que abre la base `data/processed/caso8.duckdb`.
- `graficas.py` y `estilo.py`: gráficas y apariencia (colores, tipografía).
- `ejemplos/`: muestras reales pequeñas que se ven en la página "Recorrido paso a paso"; se regeneran con `scripts/generar_ejemplos.py`.

Abrirla: `.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py`.
Antes de correr `scripts/integrar.py` o `scripts/diario.py`, **cerrar la app**: tiene la base abierta y Windows bloquea la escritura.

Siguiente paso: las tablas que la app espera están descritas en [docs/contrato_datos.md](../docs/contrato_datos.md).
