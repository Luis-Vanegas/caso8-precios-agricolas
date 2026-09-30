# Plan del equipo — AE2 (entrega 30-sep, sustentación 1-oct)

Regla de la guía: **"si no puedes explicarlo en la sustentación, no lo entregues"**. La sustentación
vale el 70 % y cualquiera de los tres puede recibir cualquier pregunta.

**Antes de empezar, confirmen dos cosas** (yo no las sé): el **número de equipo** (X en los nombres
de archivo) y la **hora límite** en el Campus Virtual del día 30.

## Reglas que se pueden perder por descuido
- El informe es un **Word de máximo 6 páginas** (sin referencias). No se califican PDF.
- **El texto del informe lo escriben ustedes.** Los archivos `docs/reporte.md`, `docs/respuestas_estructura.md`
  y `docs/guion_presentacion.md` fueron generados con IA: úsenlos para *entender*, no los copien.
- Si usan IA para un diagrama o una presentación: anexar el **prompt** y citar la herramienta en las referencias.
- 10 referencias mínimo, **5 académicas**, IEEE, y **citadas en el texto** (`docs/fuentes_y_referencias.md`).
- Todo en un **ZIP**, subido por **una sola persona** en nombre del equipo, con los nombres de los tres.

## Nombres de archivo (X = número de equipo; fecha DDMMAAAA de entrega, confirmen cuál usar)
| Archivo | Nombre |
|---|---|
| Informe (Word) | `AE2_EX_Informe_DDMMAAAA.docx` |
| 5 porqués | `Anexo1_AE2_EquipoX_DDMMAAAA` |
| Ishikawa | `Anexo2_AE2_EquipoX_DDMMAAAA` |
| Apoyo de la sustentación (Pitch) | `Anexo3_AE2_EquipoX_DDMMAAAA` |
| ZIP de evidencias | `Evidencias_AE2_EquipoX_DDMMAAAA.zip` |

## Quién hace qué

### Luis — sistema y app
1. Subir el repo a GitHub (paso 0 abajo) y compartir la carpeta de Drive.
2. **Informe 4.1.2 III** (integración multi-fuente): qué es variable clave y qué variable de integración
   (país/zona, producto, año-mes). Base: `docs/guia_powerquery.md` y `config/`.
3. **Calidad y análisis de datos** (5 %): faltantes, duplicados, hueco de 2021 de SIPSA, mayúsculas del IDEAM.
   Base: `docs/perfilado.md`, `docs/exploracion.md` y las 5 figuras de `docs/figuras/`.
4. **Diagrama del pipeline** (draw.io): fuente → `actualizar.py` → `preparar.py` → OpenRefine/Power Query → `integrar.py` → DuckDB → app.
5. La **demo de la app** en la sustentación.
6. **Conclusiones** (con A y B).

### Compañero A — el problema
1. **Los 5 porqués** (Anexo 1): parte del hecho "los precios de los alimentos se mueven sin aviso y la información llega tarde y dispersa". Hacen 4 filas de hechos y 5 columnas de "¿por qué?". Hacerlo en Miro o en papel y foto.
2. **Ishikawa** (Anexo 2): problema en la cabeza; causas por categorías (clima, mercado, datos, políticas); consecuencias.
3. Informe **4.1.1**: estado del arte (≥3 referencias, ≤250 palabras), contexto (≤250), descripción del problema (≤250, apoyada en los dos diagramas) y **objetivo SMART**.
4. **Power Query**: seguir `docs/guia_powerquery.md`, tomar capturas de pantalla (evidencia).
5. Refs a usar: [2], [3], [4], [5] de `docs/fuentes_y_referencias.md` (sección 5 dice qué aporta cada una).

### Compañero B — adquisición
1. Informe **4.1.2 I y II**: tabla de fuentes (tipo, nombre del archivo, origen, variable clave, otras variables, tiempo de lectura, contribución) y tabla de 3–5 variables objetivo. Datos: sección 1 y 2 de `docs/fuentes_y_referencias.md`.
2. Informe **4.1.3 DAQ**: sensor (el **IDEAM** es la fuente tipo sensor), qué variable genera, marca/modelo/referencia, una muestra de datos (`data/raw/ideam/.../muestra_precipitacion_cruda.json`), y las 3 preguntas de ≤50 palabras: tiempo de muestreo, resolución (delta) y **cuántos bits**.
   - El IDEAM publica lluvia cada **10 min** (verificado). Para los bits: `n = ⌈log₂(rango / resolución)⌉`; el rango y la resolución los toman de la **hoja técnica** del sensor.
   - Ojo: `verificacion_api.md` menciona un pluviómetro de referencia (Texas Electronics TE525MM, 0,1 mm por basculada) pero **aclara que no es el modelo confirmado del IDEAM**. No lo presenten como el del IDEAM, y **verifiquen sus datos en la hoja técnica** (yo no lo verifiqué).
   - Diagrama en draw.io: magnitud física → sensor → muestreo → cuantificación → codificación → dato digital.
3. **OpenRefine**: seguir `docs/guia_openrefine.md` y capturas.
4. **Referencias**: armar la lista IEEE final con lo que **realmente citan** (≥10, 5 académicas).
5. **Anexo 3**: la presentación y las **evidencias** (fotos, links de reuniones, ZIP).

## Paso a paso

### Paso 0 — Hoy, Luis, 20 minutos
1. Crear un repositorio en GitHub y subir el proyecto:
   ```powershell
   git add .
   git commit -m "Caso 8: pipeline, app e IDEAM integrado"
   git remote add origin https://github.com/<usuario>/<repo>.git
   git push -u origin main
   ```
   (si la rama se llama `master`, usar `master`). `data/raw/` y `data/interim/` no se suben (están en `.gitignore`); la base DuckDB sí.
2. Invitar a los compañeros como colaboradores. Crear la carpeta de Drive para el Word, los anexos y las evidencias.
3. Mandarles este archivo y el de fuentes y referencias.

### Paso 1 — Hoy, cada uno, 30 minutos: dejar la app corriendo
Desde PowerShell en la carpeta del proyecto:
```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m pytest tests -q
.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```
Deben ver "passed" y la app abierta. Recorran la página **"Recorrido paso a paso"**. Cada uno hace **al menos un commit** (por ejemplo, agregando su nombre y rol a `README.md`): es evidencia de trabajo en equipo.

### Paso 2 — Hoy en la noche: borradores
Cada uno hace su parte en un documento propio (Word o Google Docs). Reunión corta en Teams (**grábenla**: es evidencia) para resolver dudas.

### Paso 3 — Mañana en la mañana: juntar
1. Pegar las tres partes en un solo Word en el orden de la guía: título (≤15 palabras) → 4.1.1 → 4.1.2 → 4.1.3 → referencias.
2. Revisar que **cada referencia esté citada en el texto** y que no pase de **6 páginas**.
3. Lectura cruzada: cada uno lee la parte de otro y le hace 2 preguntas.

### Paso 4 — Mañana en la tarde: anexos, ZIP y entrega
1. Exportar los diagramas (5 porqués, Ishikawa, DAQ, pipeline) y poner los nombres correctos.
2. Armar el ZIP de evidencias: fotos, links, capturas de OpenRefine y Power Query, enlace a la grabación de Teams.
3. **Una sola persona** sube todo al Campus Virtual (o al correo de la guía si falla la plataforma) con los nombres de los tres.

### Paso 5 — Preparar la sustentación (5 min + 2 de preguntas)
El `guion_presentacion.md` está pensado para **12 minutos** y dice "cinco fuentes": la guía da **5 minutos** y hoy son **seis**. Hay que recortarlo. Reparto sugerido:

| Tiempo | Quién | Contenido |
|---|---|---|
| 0:00–1:30 | A | Problema, causas (Ishikawa) y objetivo SMART |
| 1:30–3:15 | B | Las fuentes, el sensor y cómo se digitaliza el dato |
| 3:15–5:00 | Luis | Pipeline, integración y demo de la app |

Ensayen **dos veces con cronómetro** y hagan preguntas cruzadas. La calificación es 40 % comprensión del problema, 40 % fuentes y diseño del sistema y 20 % calidad del apoyo.

### Preguntas que cada uno debe poder responder
- ¿Por qué SIPSA detecta y FAOSTAT no? (frecuencia diaria vs anual)
- ¿Qué hace OpenRefine y qué hace Power Query? ¿Y Python?
- ¿Qué hizo con los faltantes? (hueco de 2021: se declara, no se rellena)
- ¿Cómo se unen las fuentes? (producto, zona, año-mes) ¿Qué no se puede concluir?
- ¿De dónde sale el dato del sensor y qué frecuencia tiene?
- ¿Cuántos bits necesita y por qué? ¿Qué pasaría con un muestreo más lento?
- ¿Por qué se usan anomalías de clima y no valores absolutos?
