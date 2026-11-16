# Base de datos legible (Fase 1 de la reorganización)

Objetivo: que cualquiera entienda la base sin leer documentación. Rama `refactor/base-datos-legible`
(sale de `feat/app-termometro-clima`, que aún no está en `main`). Pruebas: `pytest tests -q`.
Especificación completa: `docs/prompt_reorganizacion.md`, Fase 1.

## Specs

- S1. Cada tabla lleva un prefijo que dice de dónde viene el dato: `col_`, `mundo_`, `resultado_`, `catalogo_`.
- S2. Ningún dominio de FAOSTAT se pierde: los cinco quedan en `mundo_fao_colombia`.
- S3. Un solo catálogo de productos y uno solo de zonas productoras.
- S4. Se quitan `primer_dia` y `elevacion_grilla_m`; `series` pasa a `productos_con_precio`; `flag` pasa a `calidad_dato`.
- S5. `docs/diccionario_datos.md` describe cada tabla y columna, con diagrama y tabla "antes → después".
- S6. Ningún nombre viejo queda en `src/`, `app/`, `tests/` ni `docs/`; `integrar.py` y `pytest` pasan.
- S7. Los resultados calculados no cambian.

## Tasks

- [x] T1 (S1-S4, S6, S7) inline — modelo, chequeos, indicadores, app y pruebas. Commit `be7fb67`.
- [x] T2 (S5) inline — diccionario, enlaces en README/LEEME/CLAUDE.md, perfil regenerado.
- [ ] T3 — enlazar balances alimentarios con productos (requiere equivalencias revisadas por el equipo).
- [ ] T4 — llevar la equivalencia artículo ↔ producto mensual a `catalogo_producto`.

## Log

- L1 (2026-11-15, Luis): "Tenemos 27 tablas, demasiado grande. Cómo mejorar todo esto, los nombres más
  descriptivos, para qué se usan los insumos, se necesitan las banderas para algo [...] el primer día
  siempre es el 1, solo con la columna de periodo es suficiente [...] unificar la parte de artículo y
  producto [...] que muestres qué datos son internacionales y cuáles son nacionales."
- L2. Quedaron 18 tablas, no las 14 del prompt. Llegar a 14 exigía borrar fuentes que el informe cita
  (fertilizantes, estaciones IDEAM) o mezclar tablas de grano distinto.
- L3. No se filtraron los ítems de FAO a la canasta: `app/secciones/comercio.py` muestra los 15 productos
  más importados del país (trigo, maíz), que no están en SIPSA. En su lugar, columna `producto_en_sipsa`.
- L4. Evidencia de S7: huella (filas + hash) idéntica antes y después en las tres tablas de resultados.
  29 chequeos OK, 194 pruebas pasan (incluye la prueba de humo de la app).
- L5. Riesgo: ítem 1 y 3 (formato persistido y contrato que consume la app). Sin verificador independiente.
