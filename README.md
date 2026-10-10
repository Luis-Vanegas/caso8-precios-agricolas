# Caso 8 — Volatilidad de precios agrícolas en Colombia

Integramos **6 fuentes de datos** (DANE, IDEAM, FAO, NASA, NOAA y Banco Mundial) en una sola
base y construimos una app que avisa cuando el precio de un alimento se mueve de forma anormal.

Proyecto académico — Adquisición e Integración de Datos, Ingeniería en Ciencia de Datos, ITM.

## ¿Dónde está cada cosa?

Cada carpeta tiene un `LEEME.md` corto que explica su contenido. Los términos técnicos
(raw, fact, puente, q-valor…) están en el [glosario](documentos/LEEME.md#glosario).

| Carpeta | Qué hay | Cuándo abrirla |
|---|---|---|
| [`app/`](app/LEEME.md) | La app Streamlit: menú, páginas, estilo y gráficas | Para cambiar o revisar lo que se ve en pantalla |
| [`config/`](config/LEEME.md) | Tablas de referencia hechas a mano: homologación SIPSA-FAO, mercados, zonas productoras | Para agregar un producto o un mercado |
| [`data/`](data/LEEME.md) | Los datos: crudos, intermedios y la base final | Para consultar la base o revisar qué se descargó |
| [`docs/`](docs/LEEME.md) | Documentación técnica, guías y material de sustentación | Para entender una decisión o preparar la sustentación |
| [`documentos/`](documentos/LEEME.md) | Material de consulta: artículos, guía del curso, presentaciones, borradores del informe | Para buscar bibliografía o el material del curso |
| [`odd/`](odd/LEEME.md) | Listas de tareas del proyecto | Para saber qué falta y quién lo hace |
| [`powerquery/`](powerquery/LEEME.md) | Consultas de Power Query (entregable en Excel) | Para el paso de integración en Excel |
| [`scripts/`](scripts/LEEME.md) | Los comandos que se ejecutan: descargar, limpiar, integrar | Para actualizar los datos |
| [`src/`](src/LEEME.md) | El código del pipeline, una subcarpeta por etapa | Para entender o cambiar cómo se procesan los datos |
| [`tests/`](tests/LEEME.md) | Pruebas automáticas (ninguna usa internet) | Para comprobar que nada se rompió |

**La base de datos** es `data/processed/caso8.duckdb`. Para consultarla desde la terminal
(primero **cerrar la app**: Windows bloquea el archivo mientras Streamlit lo tiene abierto):

```powershell
.venv\Scripts\python.exe -c "import duckdb; con = duckdb.connect('data/processed/caso8.duckdb', read_only=True); print(con.sql('SHOW TABLES'))"
```

**Actualizar los datos** (descargar → limpiar → integrar en un solo paso; detalle en
[docs/actualizacion_diaria.md](docs/actualizacion_diaria.md)):

```powershell
.venv\Scripts\python.exe scripts\diario.py
```

## Para el equipo: correr la app en 5 pasos (Windows)

Requisitos: [Python 3.11+](https://www.python.org/downloads/) (marcar "Add to PATH") y [Git](https://git-scm.com/downloads).
Abrir PowerShell y copiar cada línea:

```powershell
# 0. Bajar el proyecto (solo la primera vez) y entrar a la carpeta
git clone https://github.com/Luis-Vanegas/caso8-precios-agricolas.git
cd caso8-precios-agricolas

# 1. Crear el entorno de Python (solo la primera vez)
python -m venv .venv

# 2. Instalar las librerías (solo la primera vez, o si cambia requirements.txt)
.venv\Scripts\python.exe -m pip install -r requirements.txt

# 3. Comprobar que todo está bien: deben salir solo puntos y "passed"
.venv\Scripts\python.exe -m pytest tests -q

# 4. Abrir la app (se abre sola en el navegador)
.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

La base de datos (`data/processed/caso8.duckdb`) viene incluida: **no hace falta descargar nada
para ver la app**. Para entender el proyecto, empezar por la página **"Recorrido paso a paso"**.

### Cómo presentarlo (guion sugerido, 5 min)

1. **Inicio** y **Semáforo de alertas**: qué alimentos están en alerta el último mes cerrado.
2. **Recorrido paso a paso**: las 5 etapas del pipeline (traer → limpiar → homologar → unir → detectar).
3. **Detalle por producto**: elegir uno (ej. papa) y mostrar precio, volatilidad y z-score.
4. **Clima y El Niño**: el contexto (lluvia, El Niño/La Niña).
5. **Calidad de datos**: los huecos que declaramos (SIPSA 2021) y por qué no se inventan datos.

### Los datos: qué viene en el repo y qué no

| Carpeta | ¿En GitHub? | Qué es |
|---|---|---|
| `data/processed/caso8.duckdb` | Sí | La base final: con esto basta para la app |
| `data/raw/` | No (825 MB) | Descargas crudas; se regeneran con `actualizar.py` |
| `data/interim/` | No | Datos limpios intermedios; se regeneran con `preparar.py` |

Para rehacer los datos desde cero (tarda, necesita internet), correr en orden la sección
"Para actualizar los datos" de abajo. Probar una sola fuente: `scripts\actualizar.py --solo oni`.
Ver qué se descargaría sin bajar nada: `scripts\actualizar.py --dry-run`.

### Cómo aportar (cada integrante hace sus commits)

```powershell
git pull                                  # traer lo último antes de empezar
# ...hacer los cambios...
.venv\Scripts\python.exe -m pytest tests -q   # que siga todo en verde
git add .
git commit -m "docs: agrego captura de Power Query"
git push
```

Formato del mensaje: `feat:` (algo nuevo), `fix:` (corrección), `docs:` (documentos). Las tareas
pendientes están en `TASKS.md`.

## Cómo funciona (el pipeline)

```
1. Traer      scripts/actualizar.py   descarga cada fuente a data/raw/  (sin modificarla)
2. Limpiar    scripts/preparar.py     limpia, lleva todo a meses, perfila -> data/interim/
3. Homologar  config/homologacion_productos.csv  (revisado con OpenRefine)
4. Unir       scripts/integrar.py     arma el modelo estrella en DuckDB y corre 19 chequeos
5. Detectar   src/indicators/volatilidad.py  retorno, volatilidad, z-score y alerta
```

Para actualizar los datos (cerrar la app primero, porque tiene la base abierta):

```powershell
.venv\Scripts\python.exe scripts\actualizar.py          # incluye nasa_power_diario (clima del año en curso)
.venv\Scripts\python.exe scripts\preparar.py
.venv\Scripts\python.exe scripts\integrar.py
.venv\Scripts\python.exe scripts\generar_ejemplos.py
.venv\Scripts\python.exe scripts\exploracion.py
```

## Las fuentes

| Fuente | Qué aporta | Cómo se obtiene | Frecuencia |
|---|---|---|---|
| SIPSA (DANE) | Precios mayoristas por mercado: de aquí salen las alertas | API SOAP | Diaria |
| IDEAM | Lluvia y temperatura medidas por sensores (fuente tipo sensor) | API Socrata (datos.gov.co) | 10 min / 1 h |
| FAOSTAT | Producción, comercio, balances, precio al productor | Descarga masiva (ZIP con CSV) | Anual |
| NASA POWER | Clima por zona productora (histórico + meses recientes) | API REST, endpoints mensual y diario | Mensual / diaria |
| ONI (NOAA) | El Niño / La Niña | Archivo de texto | Mensual |
| Pink Sheet (Banco Mundial) | Precios de fertilizantes y energía | Excel | Mensual |

Lo verificado de cada fuente está en `docs/verificacion_api.md`. Para agregar una fuente nueva, seguir `docs/guia_nueva_fuente.md`. Las limitaciones, en la
página "Calidad de datos" de la app.

## Estructura

```
app/               la app: streamlit_app.py (menú), paginas/ (7 páginas), secciones/, estilo.py, graficas.py, datos.py
src/acquisition/   un archivo por fuente: cómo se descarga
src/cleaning/      cómo se limpia cada fuente
src/integration/   el modelo estrella en DuckDB y sus chequeos
src/indicators/    los cálculos de volatilidad y alertas
scripts/           los comandos que se corren
config/            tablas que escribimos a mano (homologación, zonas, mercados)
tests/             pruebas automáticas (ninguna usa internet)
docs/              reporte, verificación de fuentes, perfilado, exploración y figuras
```

## Si algo falla

| Síntoma | Qué hacer |
|---|---|
| `ModuleNotFoundError: plotly` | Repetir el paso 2 (se agregó plotly a requirements.txt) |
| `IO Error ... being used by another process` | Cerrar la app antes de correr `integrar.py` |
| La app dice "No existe caso8.duckdb" | Correr `actualizar.py`, `preparar.py` e `integrar.py` |
| `python` no se reconoce | Reinstalar Python marcando "Add to PATH" |
| PowerShell no deja activar scripts | No hace falta activar: usar siempre `.venv\Scripts\python.exe` como arriba |
| `git push` pide permiso | Pedirle a Luis que te agregue como colaborador en GitHub |
