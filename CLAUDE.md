# CLAUDE.md — Caso 8: volatilidad de precios agricolas (ITM)

Contexto para Claude Code. Leer antes de tocar el repo.

## Que es

Proyecto academico de Adquisicion e Integracion de Datos (ITM, 2.o semestre). Pipeline en
Python que integra 6 fuentes en DuckDB y una app Streamlit que alerta cuando un precio
mayorista se mueve de forma anormal. El equipo tiene poca experiencia en Python: el codigo
tiene que poder explicarse en una sustentacion de 5 minutos.

## Comandos (Windows, desde la raiz)

```
.venv\Scripts\python.exe scripts\actualizar.py          # descarga lo nuevo (--solo <fuente>, --dry-run)
.venv\Scripts\python.exe scripts\preparar.py            # limpia, perfila, escribe data/interim
.venv\Scripts\python.exe scripts\integrar.py            # modelo estrella + 29 chequeos
.venv\Scripts\python.exe scripts\exploracion.py         # figuras de exploracion -> docs/figuras
.venv\Scripts\python.exe scripts\generar_ejemplos.py    # muestras reales para la app
.venv\Scripts\python.exe -m pytest tests -q             # ninguna prueba toca la red
.venv\Scripts\python.exe -m streamlit run app\streamlit_app.py
```

Cerrar la app antes de `integrar.py`: tiene la base abierta y Windows bloquea la escritura.

## Estructura

- `src/acquisition/` un modulo por fuente, todos con `estado()` y `descargar()` (contrato en `src/common/modelos.py`)
- `src/cleaning/` limpieza por fuente; `src/integration/modelo.py` el modelo estrella (SQL sobre parquet)
- `src/indicators/volatilidad.py` retorno log, volatilidad, z-score y alertas
- `src/indicators/vigilancia.py` correlaciones con rezago y lista de vigilancia (pistas, no prediccion)
- `app/streamlit_app.py` solo el menu; paginas en `app/paginas/`; estilo en `app/estilo.py`; graficas en `app/graficas.py`; datos en `app/datos.py`
- `config/` homologacion SIPSA-FAO, zonas productoras, coordenadas de mercados

## Reglas del proyecto

1. **Verificar contra la fuente real antes de escribir codigo.** Ningun supuesto de documentacion sin probar. Lo verificado va en `docs/verificacion_api.md`.
2. **Datos crudos inmutables** en `data/raw/<fuente>/<fecha>/`. Nunca se editan.
3. **Pruebas sin red.** Las fixtures son recortes de respuestas reales.
4. **Nada de interpolar huecos largos** ni rellenar con datos inventados. Un hueco se declara.
5. Comentarios del codigo en espanol sin tildes; textos que ve el usuario en la app, con tildes.
6. Codigo simple y comentado: el equipo debe entender cada linea.
7. El informe del curso lo redacta el equipo (la guia AE2 prohibe texto de IA en el informe). Claude puede dar datos, tablas, codigo y explicaciones, no parrafos para pegar.

## Trabajo en paralelo (dos sesiones de Claude)

- Claude 1: carpeta `AdquiDatos`, rama `feat/datos-clima-oferta` (datos, estadistica).
- Claude 2: carpeta `AdquiDatos-claude2`, rama `feat/app-canasta-clima` (app, diseno, OpenRefine, Power Query). Arranca leyendo `odd/claude2_inicio.md`.
- Quien toca que archivo: tabla "Reparto" en `odd/tasks/clima-oferta-precio.md`. Las tablas que se intercambian: `docs/contrato_datos.md`.
- Nadie commitea `data/processed/caso8.duckdb` salvo Claude 1 en su PR de datos.

## Trampas conocidas

- SIPSA: el endpoint del WSDL (HTTP) no procesa SOAP; usar HTTPS y SOAP 1.2.
- SIPSA no tiene datos de 2021-01 a 2022-01. Los retornos solo se calculan entre meses consecutivos.
- SIPSA renombro CUCUTA -> SAN JOSE DE CUCUTA en dic. 2022 (`MERCADOS_RENOMBRADOS` en `src/cleaning/sipsa.py`).
- El ultimo mes esta abierto (`mes_cerrado = False`): la portada usa el ultimo mes cerrado.
- NASA POWER mensual publica con meses de rezago (el 2026-09-11 llegaba a 2025; el 2026-09-22, a julio de 2026) y `-999` es "sin dato". `nasa_power_diario.py` completa los meses recientes; `unir_clima` da prioridad al mensual.
- Rezagos en correlaciones: siempre en meses de calendario (`vigilancia.rezagar`), nunca `shift()` sobre filas, por el hueco de 2021.
- FAOSTAT API exige token; la carga historica sale de las descargas masivas.
- IDEAM (datos.gov.co) ~116 M de lecturas: se agrega en el servidor con SoQL. Supuestos pendientes de verificar con `scripts/probe_ideam.py`.
- Entorno del equipo: pandas 3.x y Streamlit 1.6x. Probar con esas versiones.
- En pandas, `alerta` es Categorical: convertir con `.astype(str)` antes de `map`.
