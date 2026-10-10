# src/ — el código del pipeline

Los nombres de las carpetas quedan en inglés porque de ellos dependen los imports y las pruebas. Equivalencias:

| Carpeta | En español | Qué hace |
|---|---|---|
| `acquisition/` | adquisición | Un módulo por fuente; todos tienen `estado()` y `descargar()` |
| `cleaning/` | limpieza | Limpia cada fuente y homologa productos |
| `profiling/` | perfilado | Describe cada tabla limpia (resultado en `docs/perfilado.md`) |
| `integration/` | integración | Modelo estrella (`modelo.py`) y chequeos (`verificacion.py`) |
| `indicators/` | indicadores | Volatilidad, alertas, vigilancia, sensibilidad, quiebres y pronóstico |
| `common/` | común | Rutas, descargas HTTP, registro y el contrato de las fuentes (`modelos.py`) |

Qué NO hacer: no renombrar carpetas ni módulos.

Siguiente paso: [docs/guia_nueva_fuente.md](../docs/guia_nueva_fuente.md) recorre una fuente de punta a punta.
