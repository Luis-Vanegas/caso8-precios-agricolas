# Instrucciones para Claude 2

Sos **Claude 2**. Trabajás en paralelo con otra sesión (Claude 1) sobre el mismo repositorio,
pero en **otra carpeta y otra rama**, para no pisarse.

## Antes de tocar nada, leé en este orden
1. `CLAUDE.md` (reglas del proyecto; son obligatorias)
2. `odd/tasks/clima-oferta-precio.md` (tu lista de tareas: las que empiezan con `C2-`)
3. `docs/contrato_datos.md` (las tablas que Claude 1 va a entregar y que tu app lee). **La sección "Jerarquía de productos y unidades" es obligatoria**: nunca mezcles variedades ni unidades
4. `app/estilo.py` y `app/streamlit_app.py` (cómo está hecha la app hoy)

## Tu espacio
- Carpeta: `C:\Users\LENOVO\Pictures\AdquiDatos-claude2`
- Rama: `feat/app-canasta-clima` (ya creada; no cambies de rama)
- Solo editás los archivos que la tabla "Reparto" te asigna. Si necesitás cambiar algo de Claude 1
  (`src/`, `scripts/`, `requirements.txt`, ...), dejalo anotado en `TASKS.md` bajo
  "## Pedidos de Claude 2 a Claude 1" y seguí con otra tarea.
- **Nunca** hagas `git add` de `data/processed/caso8.duckdb`.

## Python y la app
El entorno virtual está en la carpeta de Claude 1. No instales paquetes; usalo así:

```
..\AdquiDatos\.venv\Scripts\python.exe -m pytest tests -q
..\AdquiDatos\.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py --server.port 8502
```

La base `data/processed/caso8.duckdb` de tu carpeta es la copia de `main`. Las tablas nuevas del
contrato aparecen cuando Claude 1 fusione su PR y vos hagas `git rebase origin/main`. Mientras
tanto, cada página nueva muestra un aviso amable si su tabla todavía no existe (nunca un traceback).

## Cómo trabajar
1. Una tarea `C2-xx` a la vez. Al terminarla: pruebas en verde, commit pequeño con
   Conventional Commits en español (ej. `feat(app): pagina del mapa por departamento`),
   **sin** líneas de atribución de IA, y marcá la tarea con `[x]` en `odd/tasks/clima-oferta-precio.md`.
2. Verificá cada página en el navegador (puerto 8502), no solo leyendo el código.
3. Para el diseño seguí la skill `diseno-interfaz`: primero `DESIGN.md` (C2-01), después las páginas.
4. Cuando tengas varias tareas listas:
   ```
   git fetch origin
   git rebase origin/main
   ..\AdquiDatos\.venv\Scripts\python.exe -m pytest tests -q
   git push -u origin feat/app-canasta-clima
   gh pr create --base main --title "feat(app): ..." --body "..."
   ```
   Si las pruebas pasan, fusioná con `gh pr merge --squash --delete-branch` y después
   recreá la rama desde `main` actualizado para seguir.

## Empezá por
C2-01 (`DESIGN.md`), luego C2-02 (OpenRefine) y C2-04 (semáforo con los datos que ya existen).
