# Contrato de datos: tablas nuevas de la fase "clima → oferta → precio"

Este documento es el acuerdo entre las dos sesiones de trabajo:

- **Claude 1** (carpeta `AdquiDatos`, rama `feat/datos-clima-oferta`) construye estas tablas en `data/processed/caso8.duckdb`.
- **Claude 2** (carpeta `AdquiDatos-claude2`, rama `feat/app-canasta-clima`) las lee desde la app.

Regla: **los nombres de tabla y columna de este archivo no se cambian sin avisar en `TASKS.md`**.
Si una tabla todavía no existe en la base, la app muestra un aviso ("disponible cuando se integre la fuente X") en lugar de fallar.

Todas las tablas usan la llave de tiempo `periodo = anio * 100 + mes` (ej. `202503`) cuando son mensuales.

## Fuentes nuevas (verificadas el 2026-10-09 contra la API real)

| Fuente | Método / URL | Cobertura verificada |
|---|---|---|
| SIPSA abastecimiento | SOAP `promedioAbasSipsaMesMadr` (mismo endpoint que SIPSA) | 194 productos, 34 mercados, 2020-02 a 2026-07, toneladas por mes |
| SIPSA precios semanales | SOAP `promediosSipsaSemanaMadr` | 351 productos, 80 mercados, solo los últimos ~12 meses (ventana móvil) |
| Open-Meteo observado | `archive-api.open-meteo.com/v1/archive` | Diario, llega hasta ayer, sin token |
| Open-Meteo pronóstico | `api.open-meteo.com/v1/forecast` | 16 días, sin token |
| Open-Meteo estacional | `seasonal-api.open-meteo.com/v1/seasonal` | ~6 meses, varios miembros de ensamble |

## Tablas que entrega Claude 1

### `fact_abastecimiento` (mensual)
| Columna | Tipo | Descripción |
|---|---|---|
| `mercado` | texto | Nombre SIPSA de la central, ej. `Bogotá, D.C., Corabastos` |
| `ciudad` | texto | Ciudad de la central |
| `departamento` | texto | Departamento de la central |
| `dpto_codigo` | texto(2) | Código DANE del departamento, ej. `05` (llave del mapa) |
| `producto` | texto | Nombre SIPSA tal cual |
| `producto_canonico` | texto | Nombre agrupado (ver `config/productos_canonicos.csv`); nulo si aún no está homologado |
| `anio`, `mes`, `periodo` | entero | Mes |
| `toneladas` | decimal | Toneladas que entraron a la central ese mes |

### `fact_precio_semanal`
| Columna | Tipo | Descripción |
|---|---|---|
| `mercado`, `ciudad`, `departamento`, `dpto_codigo` | texto | Igual que arriba |
| `producto`, `producto_canonico` | texto | Igual que arriba |
| `grupo` | texto | Grupo de la canasta (ej. `Cereales`, `Proteínas`, `Tubérculos`); nulo si no está homologado |
| `semana_inicio` | fecha | Primer día de la semana |
| `anio`, `mes`, `periodo` | entero | Mes al que pertenece la semana |
| `precio_cop_kg`, `precio_min`, `precio_max` | decimal | Pesos por kilo |

### `fact_clima_diario`
| Columna | Tipo | Descripción |
|---|---|---|
| `departamento`, `dpto_codigo` | texto | Zona productora |
| `fecha` | fecha | Día |
| `precipitacion_mm` | decimal | Lluvia del día |
| `temp_max`, `temp_min` | decimal | °C |
| `tipo` | texto | `observado` o `pronostico` |
| `fuente` | texto | `open-meteo` |

### `fact_pronostico_estacional` (mensual)
| Columna | Tipo | Descripción |
|---|---|---|
| `departamento`, `dpto_codigo` | texto | Zona productora |
| `anio`, `mes`, `periodo` | entero | Mes pronosticado |
| `precip_p10`, `precip_p50`, `precip_p90` | decimal | Lluvia del mes (mm) según los miembros del ensamble |
| `anomalia_p50` | decimal | `precip_p50` menos el promedio histórico de ese mes |

### `indicador_sensibilidad_clima`
Una fila por producto (y departamento productor cuando aplique). Responde "¿qué tanto afecta el clima?".
| Columna | Tipo | Descripción |
|---|---|---|
| `producto`, `departamento` | texto | |
| `variable` | texto | `lluvia`, `abastecimiento`, `oni` |
| `rezago_meses` | entero | 0 a 6 |
| `coeficiente` | decimal | Efecto estimado (signo = dirección) |
| `p_valor` | decimal | Significancia |
| `n` | entero | Meses usados |
| `metodo` | texto | Ej. `panel_efectos_fijos`, `spearman` |

### `indicador_quiebres` (prueba de Chow)
| Columna | Tipo | Descripción |
|---|---|---|
| `producto`, `mercado` | texto | |
| `periodo_quiebre` | entero | Mes candidato a quiebre |
| `f_chow`, `p_valor` | decimal | Estadístico F y su p |
| `hay_quiebre` | booleano | `p_valor < 0,05` |

### `pronostico_precio`
| Columna | Tipo | Descripción |
|---|---|---|
| `producto`, `mercado` | texto | |
| `periodo` | entero | Mes |
| `tipo` | texto | `real` o `pronostico` |
| `valor`, `lim_inf`, `lim_sup` | decimal | Precio y banda (80 %) |
| `modelo` | texto | Nombre del modelo |
| `mae_modelo`, `mae_ingenuo` | decimal | Error medio en la validación contra el pasado (el modelo solo se presenta si `mae_modelo < mae_ingenuo`) |

### Cambio en una tabla existente
- `dim_mercado` gana la columna `dpto_codigo` (código DANE de 2 dígitos) para unir con el mapa.

## Archivos que entrega Claude 2 y consume Claude 1

| Archivo | Columnas | Cómo se produce |
|---|---|---|
| `config/productos_canonicos.csv` | `producto_sipsa`, `producto_canonico`, `grupo`, `en_canasta` | OpenRefine (clustering de los 351 nombres), exportado a CSV; el JSON de operaciones va a `data/openrefine/` |
| `config/geo/colombia_departamentos.geojson` | propiedad `DPTO` = código DANE | Descarga verificada; documentar origen y licencia en `docs/fuentes_app.md` (archivo propio de Claude 2) |
