# Tareas del proyecto

## 🔴 Para el usuario (bloquean o requieren acción humana)
- [ ] Crear cuenta en el Developer Portal de FAO y obtener el token de la API
- [ ] Crear el archivo `.env` a partir de `.env.example` y cargar `FAOSTAT_API_KEY`
- [ ] Crear `.env.example` a mano (las reglas de permisos me bloquean escribir archivos `.env*`)
- [ ] Validar `precioPromedio` de SIPSA contra un boletín mensual publicado del DANE

## 🟢 Para Antigravity (rápidas, mecánicas, acotadas)
- [ ] Agregar `docs/reporte.md` y `docs/respuestas_estructura.md` vacíos con sus encabezados
- [ ] Crear `app/.streamlit/config.toml` con tema básico

## 🔵 Para Claude Code (arquitectura, lógica compleja, decisiones)
- [x] Fase 0 — verificación de las seis fuentes (`docs/verificacion_api.md`)
- [ ] Fase 1 — `src/common/` (HTTP con reintentos, caché, rutas, logging)
- [ ] Fase 1 — módulos de adquisición por fuente
- [ ] Fase 1 — `scripts/carga_inicial.py` y `scripts/actualizar.py` con `meta_actualizacion`
- [ ] Fase 2 — perfilado y limpieza + CSV para OpenRefine
- [ ] Fase 3 — guía de Power Query y carga a DuckDB
- [ ] Fase 4 — app Streamlit
- [ ] Fase 5 — documentación y presentación
