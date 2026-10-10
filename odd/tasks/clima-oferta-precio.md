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
- [x] C1-07 `indicador_quiebres`: prueba de Chow de quiebre estructural (ej. El Niño 2023-24)
- [x] C1-08 `pronostico_precio`: modelo con rezagos de lluvia, abastecimiento y ONI, validado contra el ingenuo estacional
- [x] C1-09 `actualizar.py` diario para las fuentes nuevas + documentación en `docs/verificacion_api.md`

## Tareas de Claude 2 (app, diseño y herramientas)
- [x] C2-01 `DESIGN.md` con la identidad actual de la app (paleta, tipografías, semáforo) y la dirección nueva
- [x] C2-02 `config/catalogo_articulos.csv` desde `data/openrefine/catalogo_sipsa_crudo.csv`: OpenRefine propone `producto` (clustering), una persona revisa cada grupo con las reglas de la sección "Jerarquía" de `docs/contrato_datos.md`; se completan `grupo_dane`, `unidad`, `distingue_por`, `en_canasta`. JSON en `data/openrefine/` + guía actualizada
- [x] C2-03 GeoJSON de departamentos en `config/geo/` con origen y licencia en `docs/fuentes_app.md`
- [x] C2-04 Página "Semáforo de la canasta": matriz producto × periodo con los datos que ya existen
- [x] C2-05 Página "Mapa": departamentos coloreados por **variación %** del precio (nunca por nivel: la misma "papa" es otra variedad en cada ciudad), con `dim_mercado` + GeoJSON
- [x] C2-06 Página "Clima hoy": lee `fact_clima_diario` y `fact_pronostico_estacional` (aviso si aún no existen)
- [x] C2-07 Página "La cadena": lluvia, abastecimiento y precio alineados para un producto
- [x] C2-08 Página "Pronóstico": `pronostico_precio` con banda y comparación contra el ingenuo
- [x] C2-09 Power Query: guía y consulta para la tabla de abastecimiento
- [x] C2-10 Prueba de humo de cada página nueva en `tests/test_app.py`

### Navegación del repositorio en español (pedido del 2026-10-10)
Objetivo: que un integrante que abre el repo sepa en 1 minuto dónde está cada cosa (la base, los PDF, las guías, el informe).

**Regla: NO renombrar** carpetas ni archivos de código o datos (`src/`, `src/acquisition/`, `data/raw/`, `data/interim/`, `data/processed/`, `config/*.csv`, módulos y nombres de Python). De esos nombres dependen los imports, las 170 pruebas y el pipeline; en código se queda el inglés técnico. Lo que se agrega en español es una capa de navegación encima.

- [x] C2-11 `README.md`: sección "¿Dónde está cada cosa?" al principio (tabla carpeta → qué hay → cuándo abrirla), incluyendo dónde está la base (`data/processed/caso8.duckdb`), cómo abrirla y los comandos de `scripts/diario.py`
- [x] C2-12 Un `LEEME.md` corto (5-15 líneas, en español) en cada carpeta de primer nivel y en `data/`, `src/` y `docs/`: qué hay, qué NO tocar (ej. `data/raw` es inmutable) y a dónde ir después. En `src/` traducir los nombres: acquisition = adquisición, cleaning = limpieza, integration = integración, indicators = indicadores, profiling = perfilado
- [x] C2-13 Carpeta `documentos/` para material humano, con `LEEME.md` en cada subcarpeta: `articulos/` (PDF de referencia; mover ahí el de Malau 2021 si su licencia lo permite: es acceso abierto CC BY 3.0), `curso/` (guía AE2 y rúbricas), `presentaciones/`, `informe/` (borradores del equipo; recordar que el informe lo redacta el equipo). Sumar a `.gitignore` los PDF de más de 10 MB si los hubiera
- [x] C2-14 `docs/LEEME.md`: índice de los 17 documentos agrupados (guías para el equipo / técnicos / sustentación). NO mover los archivos de `docs/`: el código y otros documentos los citan por su ruta
- [x] C2-15 Glosario en `documentos/LEEME.md` o en el `README.md`: raw, interim, processed, fact, dim, puente, backtest, q-valor, art_id, fuen_id, ENSO/ONI, en una línea cada uno
- [x] C2-16 Verificar: `pytest` en verde, la app abre, y ningún enlace de los documentos nuevos apunta a un archivo inexistente

### Mejoras de la revisión en vivo de Claude 1 (2026-10-10, app sobre la base final de `main`)
Las 14 páginas cargan sin errores. Estas mejoras salen de recorrerlas con los datos reales:

- [x] C2-17 **(la más importante)** "Semáforo de la canasta" usa los 33 productos del precio DIARIO (frutas y verduras), no la canasta familiar. Sumar una vista (o reemplazar) con `fact_precio_semanal` filtrado por `en_canasta` (286 artículos: arroz, huevo, pollo, carnes, aceite, panela, queso...), agrupable por `grupo_dane`. Ojo: el semanal solo tiene ~13 meses; mostrar variación % por semana o mes y declarar el periodo cubierto
- [x] C2-18 "Mapa": los departamentos sin dato no se dibujan y Colombia se ve recortada. Dibujar los 33 departamentos y los sin dato en gris claro, con la leyenda "sin dato"
- [x] C2-19 "La cadena": el precio sale del semanal (13 meses) y solo coincide 7 meses con lluvia y toneladas. Cuando el artículo tiene par exacto en el precio diario (ver `sensibilidad.mapa_articulos`, 24 productos, p. ej. Papa criolla, Cebolla junca, Zanahoria), usar la serie mensual de `fact_precio_mayorista` desde 2020: ~50 meses de cruce en vez de 7
- [x] C2-20 "Pronóstico": la línea del precio real une 2020 con 2022 con una recta a través del hueco de 2021. Cortarla en el hueco (regla 4 del proyecto: un hueco se declara, no se rellena; el semáforo ya lo hace bien)

## Cómo se integra
1. Cada uno trabaja en su carpeta y su rama. Commits pequeños, Conventional Commits, sin atribución de IA.
2. Antes de abrir un PR: `git fetch origin` + `git rebase origin/main` + `pytest` en verde.
3. PR con `gh pr create --base main`. Se fusiona con `gh pr merge --squash --delete-branch` solo si las pruebas pasan.
4. El que fusiona segundo hace `git rebase origin/main` y vuelve a correr las pruebas.

## Progreso y evidencia
- 2026-10-10 C1-09 (inline): `scripts/diario.py` (actualizar -> preparar -> integrar; una fuente caída no frena, una limpieza rota sí) + `docs/actualizacion_diaria.md` (la tarea programada la crea cada persona, no Claude). RED -> GREEN 3/3; suite 153. Corrida real de punta a punta: ~1 h 40 min (IDEAM es lo lento). Encontró 2 problemas, corregidos: (1) una descarga parcial de IDEAM borraba lluvia sana de descargas anteriores (Antioquia 2025, Cundinamarca 2024-2025): ahora se toma la versión más reciente de CADA archivo (`rutas.archivos_mas_recientes`), también en Open-Meteo y NASA; (2) `faostat_api` sin token marcaba error todos los días: ahora solo se registra si hay token.
- 2026-10-09 C1-08 (inline): `src/indicators/pronostico.py`. Regresión (temporada del mes destino, inercia, ONI, lluvia de la zona) vs. dos ingenuos (sin cambio, estacional); backtest de 24 orígenes sin fuga (prueba: cambiar el futuro no cambia el pasado); banda 80 % de errores reales; gana solo si es 5 % mejor. RED -> GREEN 6/6; suite 149. Bug propio atrapado antes del PR: `construir` copiaba el veredicto del horizonte 1 a los 3 horizontes; la prueba nueva falla con el bug y pasa con el arreglo. Real: el modelo gana en 11/33 productos a 1 mes, 8/33 a 2 y 4/33 a 3 (error mediano 10,1 % vs. 10,5 % del ingenuo a 1 mes).
- 2026-10-09 C1-07 (inline): `src/indicators/quiebres.py`. Primera versión (Chow sobre niveles con tendencia) descartada: daba quiebre en 81/99 por la inflación de 2022 y en 50/99 aun con precio relativo, porque la autocorrelación de residuos en niveles es 0,67 (Chow la supone 0). Versión válida: cambios mensuales del precio relativo sin temporada (autocorrelación 0,11), Chow k=1 (ritmo) + Brown-Forsythe (volatilidad), 3 fechas candidatas (202302, 202306, 202405). RED -> GREEN 6/6; suite 143. Real: 0/99 quiebres de ritmo y 0/99 de volatilidad con q<0,1 (p<0,05: 2 y 1, lo esperable por azar).
- 2026-10-09 C1-06 (inline): `src/indicators/sensibilidad.py`, 4 eslabones, sin scipy/statsmodels. Panel solo en oferta->precio (la lluvia de la zona es igual para todos los mercados: un panel por mercado inflaría n). RED -> GREEN 7/7 (recupera efectos sintéticos conocidos); suite 137. Real, 140 pruebas, hallazgos con q<0,1: ONI->lluvia 27/56 (todas negativas: El Niño seca); oferta->precio 4/24 (chócolo, zanahoria, elasticidad ~-0,05); lluvia->precio 1/36 (tomate, Norte de Santander, rezago 3, -7 % por mm/día); lluvia->oferta 0/24.
- 2026-10-09 C1-05 (inline): 4 tablas opcionales en el modelo + `dpto_codigo` y `departamento` en `dim_mercado`; 10 chequeos nuevos (29 en total). RED -> GREEN; suite 130. `integrar.py` real: los 29 chequeos OK, base 12,1 MB.
- 2026-10-09 C1-04 (inline): `sipsa_canasta.py` + `clima_open_meteo.py` + `config/departamentos.csv` (33, códigos DANE) + `config/mercados_sipsa.csv` (81 mercados por `fuen_id`, 24 departamentos). RED -> GREEN 8/8; suite 125. `preparar.py` real: semanal 230310, abastecimiento 164274, clima diario 19912, estacional 40. El `dpto_codigo` de `dim_mercado` se une en C1-05 desde `config/departamentos.csv`. Bug previo corregido: una carpeta cruda vacía tapaba la última buena (IDEAM quedaba vacío).
- 2026-10-09 C1-03 (inline): RED -> GREEN 5/5; suite 117 en verde; descarga real: 24 archivos, 19784 días observados hasta 2026-10-08.
- 2026-10-09 C1-02 (inline): RED -> GREEN 3/3; suite 112 en verde; descarga real: 230312 filas, última semana 2026-10-03. La historia se acumula por carpetas diarias en `data/raw/sipsa_semanal/`.
- 2026-10-09 C1-01 (inline, 1 módulo + prueba): RED (módulo inexistente) -> GREEN 3/3; suite 109 en verde; descarga real por `actualizar.py`: 164274 filas, último mes 2026-07, 3 llamadas idénticas (40033487 bytes).
- 2026-10-09: investigación de variedades y unidades (ver "Jerarquía" en `docs/contrato_datos.md`); el catálogo pasa de nombres a `art_id`.
- 2026-10-09: fuentes nuevas verificadas contra la API real (ver `docs/contrato_datos.md`). 106 pruebas en verde en `main`.
- 2026-10-09 (Claude 2): C2-01 hecha, `DESIGN.md` en la raiz (commit 142b3ea). Siguiente de Claude 2: C2-02 (preparar archivo y guia para que el equipo corra OpenRefine) o C2-04 (semaforo de la canasta).
- 2026-10-09 (Claude 2): C2-02 hecha (commit b05f1f0). `config/catalogo_articulos.csv` con 448 articulos en 171 productos, los 8 grupos DANE, unidad y `distingue_por`. Receta en `data/openrefine/receta_catalogo_articulos.json` y Parte 2 de `docs/guia_openrefine.md` para la revision humana (pendiente: que el equipo corra OpenRefine y exporte `catalogo_articulos_revisado.json`). 111 pruebas en verde. Dos errores encontrados y corregidos al generarlo: agrupar por la primera palabra metia las 5 papayas en "Papa", y el criterio suelto de `en_canasta` dejaba fuera al tomate de arbol (46 mercados); ahora entra por presencia (>= 20 mercados). Siguiente: C2-04 (semaforo de la canasta) o C2-03 (GeoJSON).

- 2026-10-09 (Claude 2): C2-04 hecha (commit ab82c29). Pagina `app/paginas/canasta.py`: matriz producto x periodo, celda = peor alerta entre los mercados del producto (nunca promedio de precios), hueco de SIPSA incluido vacio. Calculo en `datos.matriz_canasta` y dibujo en `graficas.matriz_semaforo`. 112 pruebas en verde. Un error encontrado al verificar: `cuantas` solo traia los productos que se encendieron alguna vez, asi que un rango sin alertas para algun producto reventaba con KeyError; la prueba de humo no lo detecto porque el rango por defecto si los tenia todos. Ajuste de `DESIGN.md`: celda sin dato blanca y sin texto "s/d". Pendiente: verificacion visual en el navegador (puerto 8502) por una persona.

- 2026-10-09 (Claude 2): rebase sobre `origin/main` con C1-05 fusionado, sin conflictos. 137 pruebas en verde; verificado en la base: `fact_abastecimiento` 164.274, `fact_precio_semanal` 230.310, `fact_clima_diario` 19.912, `fact_pronostico_estacional` 40, y `dim_mercado` ya trae `dpto_codigo`.
- 2026-10-09 (Claude 2): C2-03 hecha (commit 6a74a1d). `config/geo/colombia_departamentos.geojson` (gist de John Guerra, 33 features, 1,5 MB) + `docs/fuentes_app.md`. Verificado contra el archivo real: los 33 codigos `DPTO` calzan exactamente con `config/departamentos.csv`, pero 3 de los 33 nombres no (Bogota, Narino, San Andres), asi que el mapa une por codigo. El gist **no declara licencia**: queda anotada la ruta al MGN del DANE como alternativa oficial si el curso la exige. Siguiente: C2-05 (mapa) o C2-06 (clima hoy), que ya tienen sus tablas en la base.

- 2026-10-09 (Claude 2): C2-05 a C2-10 hechas. **Las 10 tareas de Claude 2 cerradas.** 145 pruebas en verde.
  - C2-05 `app/paginas/mapa.py` (a6eae6f): mapa por variacion %, nunca por nivel. Usa `fact_precio_semanal` (24 deptos, 351 articulos) y une por `DPTO`. 284 articulos pasan el filtro de 3+ departamentos. Error corregido al verificar: el mes por defecto era octubre, que tiene 1 semana contra 4 de un mes cerrado; ahora el defecto es el ultimo mes completo y avisa si se elige uno parcial.
  - C2-06 `app/paginas/clima_hoy.py` (b1af562): dia a dia con 16 dias de pronostico y lluvia esperada por mes con banda p10-p90, 8 zonas productoras. Error corregido: faltaba importar `TIERRA` en `graficas.py`.
  - C2-07 `app/paginas/cadena.py` (a004723): tres paneles con eje X comun. **Limite declarado en pantalla: las tres series solo coinciden en 7 meses**, y la lluvia es la del departamento de la central, no la de la zona que cultivo. El selector de departamento se ordena segun el articulo elegido.
  - C2-08 `app/paginas/pronostico.py` (cfb8e1a): solo dibuja el pronostico si `mae_modelo < mae_ingenuo`. `pronostico_precio` aun no existe (C1-08), asi que hoy muestra el aviso; la grafica se probo con una tabla sintetica del esquema del contrato.
  - C2-09 `powerquery/07_SipsaAbastecimiento.pq` (03c4924) + cifras esperadas en la guia (117.782 filas de salida, 28.326.866 t). El codigo M no se ejecuto: no hay Excel en este entorno.
  - C2-10 (328fd3f): prueba que **mueve los controles**, no solo abre la pagina. Los dos errores reales de la fase solo aparecian al mover un control. Verificada reintroduciendo el bug a proposito: falla; restaurado: pasa.
- 2026-10-09 (Claude 2): **pendientes humanos** (no los puede cerrar un agente): verificacion visual de las 5 paginas nuevas en el navegador (puerto 8502) y la revision del catalogo en OpenRefine (Parte 2 de `docs/guia_openrefine.md`). Pendiente de Claude 1: ver "Pedidos de Claude 2 a Claude 1" en `TASKS.md` (columnas del catalogo vacias en las dos tablas nuevas).

- 2026-10-10 (Claude 2): **PR #9 fusionado en `main`** (squash, commit `5aaec13`): las 10 tareas de Claude 2, 19 archivos, +2261/-12. 169 pruebas en verde desde `main` recien fusionado. Rama recreada desde `main`.
  - Antes del PR, el rebase sobre `main` con C1-06 a C1-09 rompio `app/paginas/pronostico.py`: la tabla `pronostico_precio` quedo con `producto` + `horizonte` + `gana_al_ingenuo` en vez del `art_id`/`articulo` del contrato original. **La prueba de humo lo atrapo.** Adaptada (commit en el PR): tarjeta por horizonte, MAE en % y no en pesos, y cuando el modelo no gana se grafica el ingenuo diciendo que lo es. Verificado contra la tabla real: los 33 productos abren; el aviso sale en 19 y no en los 14 que ganan.
  - Con `indicador_sensibilidad_clima` ya en la base, la pagina de la cadena muestra lo medido por eslabon (efecto, rezago, q-valor) en vez de solo prometerlo. Solo los eslabones que cruzan por `art_id`/departamento; `lluvia->precio` se declara aparte porque uso los nombres de los precios diarios.
  - No pude correr `preparar.py` en mi carpeta: `data/raw/` no se versiona y solo existe en la de Claude 1. El pedido de rellenar `producto`/`grupo_dane`/`en_canasta` queda confirmado como trabajo de Claude 1 (ahora el catalogo ya esta en `main`).

## Siguiente paso
Claude 1 arranca en C1-01. Claude 2 arranca en C2-01.
