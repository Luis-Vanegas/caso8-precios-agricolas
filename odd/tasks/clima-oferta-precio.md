# Fase: clima → oferta → precio (trabajo en paralelo)

## Objetivo
Mostrar qué tanto afecta el clima a los precios de la canasta familiar, con la cadena
**lluvia en la zona productora → toneladas que llegan al mercado → precio → semáforo**,
un mapa por departamento, el clima de hoy y un pronóstico validado contra el pasado.

## Por qué
El reto pide relacionar clima y precios y anticipar cambios. Hoy el proyecto tiene 33
productos y una lista de vigilancia débil (2 de 36 parejas con relación). Las fuentes nuevas
(abastecimiento, precios semanales, Open-Meteo) permiten la cadena completa y la canasta real.
Referencia: Malau et al. (2021), panel de efectos fijos clima → precio (Indonesia, anual).

## Restricciones
- Reglas de `CLAUDE.md`: verificar contra la fuente real, datos crudos inmutables, pruebas sin red,
  no interpolar huecos, código simple y comentado en español sin tildes.
- El modelo de pronóstico solo se presenta si le gana al modelo ingenuo en la validación.
- Correlación no es causalidad: la app lo dice en pantalla.

## Reparto (quién toca qué)

| | Claude 1 | Claude 2 |
|---|---|---|
| Carpeta | `C:\Users\LENOVO\Pictures\AdquiDatos` | `C:\Users\LENOVO\Pictures\AdquiDatos-claude2` |
| Rama | `feat/datos-clima-oferta` | `feat/app-canasta-clima` |
| Es dueño de | `src/`, `scripts/`, `tests/` (menos `test_app.py`), `config/mercados.csv`, `config/zonas_productoras.json`, `docs/contrato_datos.md`, `docs/verificacion_api.md`, `docs/fuentes_y_referencias.md`, `requirements.txt` | `app/`, `tests/test_app.py`, `DESIGN.md`, `config/catalogo_articulos.csv`, `config/geo/`, `docs/fuentes_app.md`, `docs/guia_openrefine.md`, `docs/guia_powerquery.md`, `powerquery/`, `data/openrefine/` |
| Puerto de la app | 8501 | 8502 |

Compartidos (cada uno edita solo su sección): `TASKS.md`, este archivo.
**Nadie commitea `data/processed/caso8.duckdb`** salvo Claude 1 en su PR final de datos.
Si Claude 2 necesita una librería nueva, la pide en `TASKS.md` y Claude 1 la agrega a `requirements.txt`.

## Tareas de Claude 1 (datos y estadística)
- [x] C1-01 Adquisición `sipsa_abastecimiento.py` (método `promedioAbasSipsaMesMadr`) + fixture recortada + prueba
- [x] C1-02 Adquisición `sipsa_semanal.py` (método `promediosSipsaSemanaMadr`) que acumula snapshots (la API solo da 12 meses)
- [x] C1-03 Adquisición `open_meteo.py`: observado diario, pronóstico 16 días y estacional 6 meses por zona productora
- [x] C1-00 Catálogo crudo de 448 artículos por `art_id` con `unidad_sugerida` en `data/openrefine/catalogo_sipsa_crudo.csv` (excepción al reparto: lo genera Claude 1 una sola vez)
- [x] C1-04 Limpieza de las tres fuentes por `art_id` con columna `unidad` + `dpto_codigo` en `config/mercados.csv` y `dim_mercado`
- [x] C1-05 Tablas del contrato en `src/integration/modelo.py` + chequeos de integración
- [x] C1-06 `indicador_sensibilidad_clima`: filtro ONI-lluvia por departamento + panel de efectos fijos mensual (réplica de Malau 2021)
- [ ] C1-07 `indicador_quiebres`: prueba de Chow de quiebre estructural (ej. El Niño 2023-24)
- [ ] C1-08 `pronostico_precio`: modelo con rezagos de lluvia, abastecimiento y ONI, validado contra el ingenuo estacional
- [ ] C1-09 `actualizar.py` diario para las fuentes nuevas + documentación en `docs/verificacion_api.md`

## Tareas de Claude 2 (app, diseño y herramientas)
- [ ] C2-01 `DESIGN.md` con la identidad actual de la app (paleta, tipografías, semáforo) y la dirección nueva
- [ ] C2-02 `config/catalogo_articulos.csv` desde `data/openrefine/catalogo_sipsa_crudo.csv`: OpenRefine propone `producto` (clustering), una persona revisa cada grupo con las reglas de la sección "Jerarquía" de `docs/contrato_datos.md`; se completan `grupo_dane`, `unidad`, `distingue_por`, `en_canasta`. JSON en `data/openrefine/` + guía actualizada
- [ ] C2-03 GeoJSON de departamentos en `config/geo/` con origen y licencia en `docs/fuentes_app.md`
- [ ] C2-04 Página "Semáforo de la canasta": matriz producto × periodo con los datos que ya existen
- [ ] C2-05 Página "Mapa": departamentos coloreados por **variación %** del precio (nunca por nivel: la misma "papa" es otra variedad en cada ciudad), con `dim_mercado` + GeoJSON
- [ ] C2-06 Página "Clima hoy": lee `fact_clima_diario` y `fact_pronostico_estacional` (aviso si aún no existen)
- [ ] C2-07 Página "La cadena": lluvia, abastecimiento y precio alineados para un producto
- [ ] C2-08 Página "Pronóstico": `pronostico_precio` con banda y comparación contra el ingenuo
- [ ] C2-09 Power Query: guía y consulta para la tabla de abastecimiento
- [ ] C2-10 Prueba de humo de cada página nueva en `tests/test_app.py`

## Cómo se integra
1. Cada uno trabaja en su carpeta y su rama. Commits pequeños, Conventional Commits, sin atribución de IA.
2. Antes de abrir un PR: `git fetch origin` + `git rebase origin/main` + `pytest` en verde.
3. PR con `gh pr create --base main`. Se fusiona con `gh pr merge --squash --delete-branch` solo si las pruebas pasan.
4. El que fusiona segundo hace `git rebase origin/main` y vuelve a correr las pruebas.

## Progreso y evidencia
- 2026-10-09 C1-06 (inline): `src/indicators/sensibilidad.py`, 4 eslabones, sin scipy/statsmodels. Panel solo en oferta->precio (la lluvia de la zona es igual para todos los mercados: un panel por mercado inflaría n). RED -> GREEN 7/7 (recupera efectos sintéticos conocidos); suite 137. Real, 140 pruebas, hallazgos con q<0,1: ONI->lluvia 27/56 (todas negativas: El Niño seca); oferta->precio 4/24 (chócolo, zanahoria, elasticidad ~-0,05); lluvia->precio 1/36 (tomate, Norte de Santander, rezago 3, -7 % por mm/día); lluvia->oferta 0/24.
- 2026-10-09 C1-05 (inline): 4 tablas opcionales en el modelo + `dpto_codigo` y `departamento` en `dim_mercado`; 10 chequeos nuevos (29 en total). RED -> GREEN; suite 130. `integrar.py` real: los 29 chequeos OK, base 12,1 MB.
- 2026-10-09 C1-04 (inline): `sipsa_canasta.py` + `clima_open_meteo.py` + `config/departamentos.csv` (33, códigos DANE) + `config/mercados_sipsa.csv` (81 mercados por `fuen_id`, 24 departamentos). RED -> GREEN 8/8; suite 125. `preparar.py` real: semanal 230310, abastecimiento 164274, clima diario 19912, estacional 40. El `dpto_codigo` de `dim_mercado` se une en C1-05 desde `config/departamentos.csv`. Bug previo corregido: una carpeta cruda vacía tapaba la última buena (IDEAM quedaba vacío).
- 2026-10-09 C1-03 (inline): RED -> GREEN 5/5; suite 117 en verde; descarga real: 24 archivos, 19784 días observados hasta 2026-10-08.
- 2026-10-09 C1-02 (inline): RED -> GREEN 3/3; suite 112 en verde; descarga real: 230312 filas, última semana 2026-10-03. La historia se acumula por carpetas diarias en `data/raw/sipsa_semanal/`.
- 2026-10-09 C1-01 (inline, 1 módulo + prueba): RED (módulo inexistente) -> GREEN 3/3; suite 109 en verde; descarga real por `actualizar.py`: 164274 filas, último mes 2026-07, 3 llamadas idénticas (40033487 bytes).
- 2026-10-09: investigación de variedades y unidades (ver "Jerarquía" en `docs/contrato_datos.md`); el catálogo pasa de nombres a `art_id`.
- 2026-10-09: fuentes nuevas verificadas contra la API real (ver `docs/contrato_datos.md`). 106 pruebas en verde en `main`.

## Siguiente paso
Claude 1 arranca en C1-01. Claude 2 arranca en C2-01.
