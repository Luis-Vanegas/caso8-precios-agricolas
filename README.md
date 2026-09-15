# Caso 8 — Volatilidad de precios agrícolas en Colombia

Pipeline de integración de datos y app de demostración que detecta movimientos anómalos de
precio en los mercados mayoristas del país.

Proyecto académico — Adquisición e Integración de Datos, Ingeniería en Ciencia de Datos, ITM.

## Puesta en marcha

```bash
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
```

Copiá `.env.example` a `.env` y cargá `FAOSTAT_API_KEY` si tenés token del Developer Portal de
FAO. No es obligatorio: la carga histórica sale de las descargas masivas.

## Correr el pipeline

```bash
.venv/Scripts/python.exe scripts/carga_inicial.py   # primera vez: baja todo
.venv/Scripts/python.exe scripts/preparar.py        # limpia y perfila
.venv/Scripts/python.exe scripts/integrar.py        # carga el modelo y verifica
.venv/Scripts/python.exe -m streamlit run app/streamlit_app.py
```

Para actualizar después, `scripts/actualizar.py` en lugar de `carga_inicial.py`. Los tres
scripts son idempotentes: correrlos dos veces seguidas no descarga nada de nuevo.

**Cerrá la app antes de actualizar.** Mantiene el archivo DuckDB abierto y en Windows eso
bloquea la escritura.

## Documentación

| Documento | Qué contiene |
|---|---|
| `docs/reporte.md` | Reporte del proceso, hallazgos, fortalezas y debilidades |
| `docs/respuestas_estructura.md` | Respuestas a las preguntas de ESTRUCTURA |
| `docs/verificacion_api.md` | Evidencia de la verificación de cada fuente |
| `docs/perfilado.md` | Perfilado de las tablas, generado por el pipeline |
| `docs/guia_openrefine.md` | Paso manual de homologación |
| `docs/guia_powerquery.md` | Paso manual de integración |
| `docs/guion_presentacion.md` | Guion de la presentación |

## Estructura

```
src/common/        utilidades: HTTP con reintentos, rutas, bitácora
src/acquisition/   un módulo por fuente, todos con estado() y descargar()
src/cleaning/      limpieza y homologación
src/profiling/     perfilado e inconsistencias
src/integration/   modelo estrella y chequeos de integridad
src/indicators/    volatilidad, alertas y dependencia de importaciones
scripts/           puntos de entrada
app/               Streamlit
config/            homologación de productos y zonas productoras
powerquery/        consultas M
tests/             75 pruebas, ninguna toca la red
```

## Pruebas

```bash
.venv/Scripts/python.exe -m pytest tests/ -q
```
