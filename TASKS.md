# Tareas del proyecto

## Para el equipo (antes de la entrega del 30 de septiembre)
- [x] Luis: correr `scripts/probe_ideam.py` y pegar la salida en `docs/verificacion_api.md` — encontró y corrigió un bug real (mayúsculas de `departamento`, ver sección "IDEAM — verificación del 2026-09-23")
- [x] Luis: IDEAM descargado (lluvia, 8 departamentos), `preparar.py`, `integrar.py`, `exploracion.py` y `pytest` corridos el 29-sep-2026 (ver `docs/fuentes_y_referencias.md`)
- [ ] Todos: instalar de nuevo las librerías (`pip install -r requirements.txt`, se agregó plotly)
- [ ] Todos: recorrer la página "Recorrido paso a paso" y el documento de estudio
- [ ] Ejecutar OpenRefine siguiendo `docs/guia_openrefine.md` y exportar el JSON a `data/openrefine/` (captura como evidencia)
- [ ] Ejecutar Power Query siguiendo `docs/guia_powerquery.md` (captura como evidencia)
- [ ] Copiar `.env.example` a `.env` (opcional: tokens de FAO y datos.gov.co)
- [x] Subir el repo a GitHub (privado): https://github.com/Luis-Vanegas/caso8-precios-agricolas
- [ ] Luis: invitar a cada integrante (Settings → Collaborators) y que cada uno haga al menos un commit
- [ ] Opcional: borrar `data/raw/_probe/sipsa/` (108 MB duplicados)

## Fase clima → oferta → precio (en curso)
Lista detallada y reparto entre Claude 1 y Claude 2: `odd/tasks/clima-oferta-precio.md`.

## Pedidos de Claude 2 a Claude 1
- (vacío)

## Pedidos de Claude 1 a Claude 2
- Mapa (C2-03/C2-05): el GeoJSON de john-guerra trae nombres con codificación dañada (`NARIÃ‘O`). Unir SIEMPRE por la propiedad `DPTO` contra `dpto_codigo`, nunca por nombre. Los códigos y nombres limpios están en `config/departamentos.csv` (33 departamentos).
- Ya existen en `data/interim/` (correr `preparar.py` en tu carpeta no hace falta: llegan con la base cuando fusione C1-05): `sipsa_semanal`, `sipsa_abastecimiento`, `clima_diario`, `clima_estacional`.

## Pendientes técnicos
- [ ] Validar la lista de vigilancia fuera de muestra (calcular rho con datos hasta 2024 y medir el acierto en 2025-2026)
- [ ] Completar `faostat_api.py` cuando haya token
- [ ] Validar las alertas contra eventos conocidos de desabastecimiento
- [ ] Sumar microdatos del DANE para cubrir el hueco de 2021 de SIPSA
- [ ] Refinar zonas productoras con polígonos de UPRA/EVA
- [ ] Ampliar a 6 meses los rezagos de la correlación con el ONI (el efecto aparece a los 4-5 meses)

## Hecho
- [x] Fases 0 a 5: verificación, adquisición, limpieza, homologación, modelo estrella, indicadores, reporte
- [x] Fuente de sensor IDEAM: módulo, limpieza, tablas en el modelo y 8 pruebas (pendiente carga en vivo)
- [x] Exploración de datos: 5 figuras y `docs/exploracion.md`
- [x] Corrección: mercado CÚCUTA / SAN JOSÉ DE CÚCUTA unificado (la serie estaba partida)
- [x] Corrección: el último mes se marca como abierto y no dispara alertas en la portada
- [x] Corrección: `compactar` ya no borra la base antes de reemplazarla
- [x] App rediseñada: 7 páginas, estilo propio, recorrido paso a paso, prueba de humo por página
- [x] `CLAUDE.md`, `.gitattributes` y `.env.example`
- [x] Clima 2026: `nasa_power_diario.py` completa los meses que el mensual aún no trae (5 pruebas)
- [x] Corrección: los rezagos de las correlaciones se cuentan en meses de calendario, no en filas
- [x] Página "Lo que va de 2026" y lista de vigilancia con tasa de acierto (`vigilancia.py`, 4 pruebas)
- [x] Guía `docs/guia_nueva_fuente.md`

## Estado verificado (22 de septiembre de 2026)

| Comprobación | Resultado |
|---|---|
| Pruebas | 103 (94 de pipeline + 9 de la app), ninguna usa internet |
| Chequeos de integridad | 19, todos en verde |
| App | 8 páginas, todas abren sin errores con Streamlit 1.63 y pandas 3.0 |
| Base DuckDB | 18 tablas, 20 mercados, 5,8 MB |

## Actualización del 29 de septiembre de 2026
- [x] SIPSA, NASA POWER, ONI y Pink Sheet actualizados; base reconstruida (19 chequeos en verde, 105 pruebas)
- [x] IDEAM (lluvia) integrado: 8 departamentos, 600 filas departamento-mes. Faltaban Cundinamarca 2024-2025 y Antioquia completa
- [x] Corrección: `BOYACA` y `Boyaca` quedaban como dos departamentos; ahora `a_vocabulario_config` los unifica
- [x] `matplotlib` faltaba en `requirements.txt` (lo importa `exploracion.py`)
- [ ] Temperatura del IDEAM (`sbwg-7ju4`): verificada pero no descargada; la app solo muestra lluvia
- [ ] `docs/reporte.md` dice "datos actualizados al 15 de septiembre": actualizar la fecha y las cifras al entregar
