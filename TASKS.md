# Tareas del proyecto

## 🔴 Para el usuario (bloquean o requieren acción humana)
- [ ] Crear `.env.example` a mano con `FAOSTAT_API_KEY=` y `CONTACT_EMAIL=` (mis permisos bloquean escribir archivos `.env*`), copiarlo a `.env`
- [ ] Obtener el token del Developer Portal de FAO y cargarlo en `.env`. Sin él, `faostat_api` reporta error y las otras cinco fuentes siguen funcionando
- [ ] **Ejecutar OpenRefine** siguiendo `docs/guia_openrefine.md` y exportar el JSON de operaciones a `data/openrefine/`. La receta está escrita en `receta_homologacion.json` pero NO fue ejecutada: no tengo OpenRefine
- [ ] **Ejecutar Power Query** siguiendo `docs/guia_powerquery.md`. El código M está escrito pero NO fue ejecutado: no tengo Excel. Compará contra las cifras de "Resultado esperado"
- [ ] Decidir si las zonas productoras se refinan con polígonos de UPRA/EVA o se quedan en capitales departamentales
- [ ] Revisar las 9 inconsistencias reales de comercio en `docs/perfilado.md`
- [ ] Opcional: borrar `data/raw/_probe/sipsa/` (108 MB duplicados). No lo toco por la regla de datos crudos inmutables
- [ ] Publicar la app en Streamlit Community Cloud (Fase 4.5)

## 🟢 Para Antigravity (rápidas, mecánicas, acotadas)
- [ ] Ampliar `config/zonas_productoras.json` con más productos foco, respetando los nombres exactos de SIPSA
- [ ] Revisar ortografía y tildes de los documentos de `docs/`

## 🔵 Para Claude Code (arquitectura, lógica compleja, decisiones)
- [x] Fase 0 — verificación de las seis fuentes (`docs/verificacion_api.md`)
- [x] Fase 1 — adquisición, bitácora de frescura, scripts idempotentes
- [x] Fase 2 — limpieza, perfilado y CSV para OpenRefine (`docs/perfilado.md`)
- [x] Fase 2 — homologación SIPSA ↔ FAOSTAT validada contra los datos
- [x] Fase 3 — modelo estrella en DuckDB con 19 chequeos de integridad
- [x] Fase 3 — consultas M de Power Query y guía
- [x] Fase 4 — indicadores de volatilidad y app Streamlit de seis páginas
- [x] Fase 5 — reporte, respuestas ESTRUCTURA y guion de presentación
- [ ] Completar `faostat_api.py` cuando haya token (rutas y esquema de cabecera)
- [ ] Validar los métodos `*Madr` de SIPSA, que pueden filtrar por la bandera `enviado`
- [ ] Validar las alertas contra eventos conocidos de desabastecimiento
- [ ] Sumar los microdatos del DANE 2013–2019 para extender la historia de precios

## Estado verificado

| Comprobación | Resultado |
|---|---|
| Tests | 75, ninguno toca la red |
| Chequeos de integridad | 19, todos en verde |
| Dirección de dependencias | correcta |
| Idempotencia del pipeline | verificada |
| App Streamlit | 6 páginas, todas renderizan |
| Base DuckDB | 18 tablas, 249 563 filas, 5,8 MB |
