# Cómo conectar una fuente nueva y analizarla

Guía para el equipo. Usa como ejemplo real lo que hicimos el 22 de septiembre de 2026: agregar
**NASA POWER diario** para tener el clima de 2026, que el endpoint mensual todavía no traía
completo.

Son siete pasos. Los archivos de ejemplo están en el repositorio: se pueden abrir y comparar.

---

## Paso 1 — Verificar la fuente ANTES de escribir código

La regla del proyecto: ningún supuesto sin probarlo contra el servicio real.

Qué verificamos y cómo:

| Pregunta | Cómo se comprobó | Resultado |
|---|---|---|
| ¿Hasta qué fecha llega? | `GET /api/temporal/daily/configuration` | Hasta el 2026-09-22 |
| ¿Qué pasa con los días sin dato? | Pedir del 1 ago al 20 sep 2026 | Los últimos 3 días llegan en `-999` |
| ¿Mismas unidades que el mensual? | Leer `parameters.units` de las dos respuestas | Sí: mm/día y °C |
| ¿Se pueden pegar las dos series? | Promediar los días de 2025 y comparar con el mensual | Iguales: julio 6,15 = 6,15 |

Esta verificación destapó algo: **el endpoint mensual cambió**. El 11 de septiembre llegaba
hasta 2025; el 22 ya traía enero a julio de 2026. Agosto y septiembre venían en `-999`.
Moraleja: una verificación vale para el día en que se hizo, y hay que repetirla.

Todo lo verificado se anota en `docs/verificacion_api.md`.

## Paso 2 — Escribir el módulo de adquisición

Archivo: `src/acquisition/nasa_power_diario.py`.

Todas las fuentes cumplen el mismo contrato, así el orquestador las trata igual:

```python
def estado() -> EstadoFuente:        # ¿está disponible? ¿hasta qué fecha llega? (no descarga nada)
def descargar(desde=None, forzar=False) -> ResultadoDescarga:   # baja y guarda en data/raw/
```

Reglas:

- Lo descargado se guarda **tal cual llega** en `data/raw/<fuente>/<fecha de hoy>/`.
- Usar `sesion()` de `src/common/http.py`: ya trae reintentos si la API falla.
- Si una zona falla, se anota el error y se sigue con las demás.

## Paso 3 — Registrarla en el orquestador

En `scripts/actualizar.py`, una línea en el diccionario `FUENTES`:

```python
"nasa_power_diario": nasa_power_diario,
```

Desde ese momento, `actualizar.py` la consulta, la descarga y la anota en la bitácora
`meta_actualizacion`. Se puede probar sola con `--solo nasa_power_diario`.

## Paso 4 — Limpiar y llevar a la frecuencia común (mes)

Función `a_mensual` en el módulo, y `limpiar_clima_diario` en `src/cleaning/complementarias.py`:

1. Los `-999` se vuelven vacíos **antes** de promediar. Un solo `-999` hundiría el promedio.
2. Se promedian los días de cada mes y se cuenta cuántos tenían dato (`dias_con_dato`).
3. Un mes con menos de 10 días no se usa.

## Paso 5 — Integrar sin duplicar

Función `unir_clima`: pega los meses nuevos detrás de la serie mensual.

- Si un mes está en las dos fuentes, **gana el mensual**, que es la versión oficial.
- La columna `fuente` dice de dónde salió cada fila (`mensual` o `diario`).
- La anomalía se calcula **después** de unir, así los meses nuevos se comparan contra el
  mismo promedio histórico.

En `src/integration/modelo.py`, la tabla `fact_clima` ahora trae `fuente` y `dias_con_dato`.

## Paso 6 — Probar

Archivo: `tests/test_nasa_diario.py`. La fixture es una respuesta **real** recortada
(`tests/fixtures/nasa_power_diario_boyaca.json`), así las pruebas no necesitan internet.

| Prueba | Qué garantiza |
|---|---|
| agosto = promedio de sus 31 días | El cálculo básico está bien |
| los `-999` no entran | Septiembre cuenta 17 días, no 20 |
| mes con pocos días se descarta | No se usan promedios poco confiables |
| gana el mensual | No hay filas duplicadas |
| sin datos diarios igual existen las columnas | El modelo no se cae si la fuente falla |

```
.venv\Scripts\python.exe -m pytest tests -q
```

## Paso 7 — Correr el pipeline y analizar

```
.venv\Scripts\python.exe scripts\actualizar.py --solo nasa_power
.venv\Scripts\python.exe scripts\actualizar.py --solo nasa_power_diario
.venv\Scripts\python.exe scripts\preparar.py
.venv\Scripts\python.exe scripts\integrar.py
.venv\Scripts\python.exe scripts\exploracion.py
```

Y abrir la app en la página **"Lo que va de 2026"**, que se arma sola con lo nuevo:

- precios del último mes contra el mismo mes del año anterior;
- alertas por mes del año;
- ONI y lluvia de cada zona productora mes a mes;
- la **lista de vigilancia**: productos cuyo precio se ha movido junto con la lluvia de 1 a 3
  meses antes (`src/indicators/vigilancia.py`), con su tasa de acierto histórica.

---

## Checklist para cualquier fuente nueva

- [ ] Verificada contra el servicio real y anotada en `docs/verificacion_api.md`
- [ ] Módulo en `src/acquisition/` con `estado()` y `descargar()`
- [ ] Registrada en `FUENTES` de `scripts/actualizar.py`
- [ ] Limpieza que la deja en grano mensual y con la variable de integración (año-mes, departamento o producto)
- [ ] Unida al modelo en `src/integration/modelo.py` sin duplicar filas
- [ ] Pruebas con una fixture real y sin internet
- [ ] Documentada en el README y en la página "Calidad de datos" si tiene limitaciones
