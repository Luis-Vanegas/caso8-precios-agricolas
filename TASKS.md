# Tareas del proyecto

## 🔴 Para el usuario (bloquean o requieren acción humana)
- [ ] Crear cuenta en el Developer Portal de FAO y obtener el token de la API
- [ ] Crear `.env.example` a mano con `FAOSTAT_API_KEY=` y `CONTACT_EMAIL=` (las reglas de permisos me bloquean escribir archivos `.env*`), copiarlo a `.env` y cargar el token
- [ ] Validar `precioPromedio` de SIPSA contra un boletín mensual publicado del DANE
- [ ] Decidir si las coordenadas de `config/zonas_productoras.json` se refinan con polígonos de UPRA/EVA o se quedan en capitales departamentales
- [ ] Opcional: borrar `data/raw/_probe/sipsa/` (108 MB duplicados de la descarga real). No lo toco por la regla de datos crudos inmutables

## 🟢 Para Antigravity (rápidas, mecánicas, acotadas)
- [ ] Agregar `docs/reporte.md` y `docs/respuestas_estructura.md` vacíos con sus encabezados
- [ ] Crear `app/.streamlit/config.toml` con tema básico
- [ ] Ampliar `config/zonas_productoras.json` con más productos foco

## 🔵 Para Claude Code (arquitectura, lógica compleja, decisiones)
- [x] Fase 0 — verificación de las seis fuentes (`docs/verificacion_api.md`)
- [x] Fase 1 — `src/common/` (HTTP con reintentos, rutas, bitácora en DuckDB)
- [x] Fase 1 — módulos de adquisición por fuente
- [x] Fase 1 — `carga_inicial.py` y `actualizar.py` con `meta_actualizacion`
- [ ] Fase 1 — completar `faostat_api.py` cuando haya token (rutas y esquema de cabecera)
- [ ] Fase 1 — validar los métodos `*Madr` de SIPSA, que pueden filtrar por la bandera `enviado`
- [ ] Fase 2 — perfilado y limpieza + CSV para OpenRefine
- [ ] Fase 3 — guía de Power Query y carga a DuckDB
- [ ] Fase 4 — app Streamlit
- [ ] Fase 5 — documentación y presentación
