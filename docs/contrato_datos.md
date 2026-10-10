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

## Jerarquía de productos y unidades (leer antes de cualquier tabla)

Investigado el 2026-10-09 con los datos del DANE y la metodología SIPSA-P.

```
Grupo DANE (8 oficiales)      Tubérculos, raíces y plátanos
  └ Producto                  Papa criolla
      └ Artículo (art_id)     Papa criolla limpia   <- aquí se analiza
```

- **Grupos DANE** (metodología SIPSA-P): Verduras y hortalizas · Frutas · Tubérculos, raíces y plátanos · Granos y cereales · Huevos y lácteos · Carnes · Pescados · Productos procesados.
- **La llave es `art_id`** (el `artiId` del DANE), nunca el nombre. Es el mismo código en precios semanales y en abastecimiento (97 artículos en común, 0 diferencias de nombre).
- Un artículo se distingue de otro del mismo producto por **variedad** (papa capira / suprema), **calidad** (huevo B / A / AA / extra según NTC 1240; arroz de primera / segunda), **presentación** (criolla limpia / sucia; plátano verde / maduro; fresco / congelado), **origen** (cebolla junca Aquitania / Berlín; nacional / importado) o **procesado** (arveja en vaina / seca / enlatada).
- **Unidades del precio** (metodología SIPSA-P, p. 16): pesos por **kg**, salvo huevo y bocadillo (**por unidad**) y aceite, jugo y vinagre (**por litro**), aunque el campo de la API se llame `promedioKg`. El abastecimiento siempre va en toneladas.

**Reglas**
1. Se analiza siempre por artículo. **Nunca se promedian precios de artículos distintos.**
2. Un valor de "producto" (ej. "la papa") es la **mediana de las variaciones %** de sus artículos, nunca el promedio de sus precios.
3. Nunca se mezclan unidades distintas en una misma gráfica o cálculo.
4. Los precios diarios (`promediosSipsaCiudad`, los 33 productos actuales) usan otros códigos. Indicio fuerte: su "Papa negra*" es una variedad distinta en cada ciudad (capira en Bogotá, Medellín y Cali; única en Barranquilla), y su "Papa criolla" es limpia en unas ciudades y sucia en otras. Por eso **entre ciudades se comparan variaciones %, nunca niveles de precio** (incluido el mapa).
5. Nombres engañosos: el tomate de árbol **no** es tomate; "Papaya" empieza por "Papa". No se agrupa por la primera palabra del nombre.
6. Artículos con 2 mercados o menos (43 de 351) no van al mapa.
7. La correspondencia entre la granularidad de precios y de abastecimiento se declara a mano en el catálogo (ej. abastecimiento tiene una sola "Papa criolla" y una "Papa R-12" sin color; precios separa criolla limpia/sucia y R-12 negra/roja).

## Tablas que entrega Claude 1

### `fact_abastecimiento` (mensual)
| Columna | Tipo | Descripción |
|---|---|---|
| `mercado` | texto | Nombre SIPSA de la central, ej. `Bogotá, D.C., Corabastos` |
| `ciudad` | texto | Ciudad de la central |
| `departamento` | texto | Departamento de la central |
| `dpto_codigo` | texto(2) | Código DANE del departamento, ej. `05` (llave del mapa) |
| `art_id` | entero | Código del artículo en el DANE (llave) |
| `articulo` | texto | Nombre DANE tal cual, ej. `Papa criolla` |
| `producto`, `grupo_dane` | texto | Del catálogo (`config/catalogo_articulos.csv`); nulo si aún no está homologado |
| `anio`, `mes`, `periodo` | entero | Mes |
| `toneladas` | decimal | Toneladas que entraron a la central ese mes |

### `fact_precio_semanal`
| Columna | Tipo | Descripción |
|---|---|---|
| `mercado`, `ciudad`, `departamento`, `dpto_codigo` | texto | Igual que arriba |
| `art_id`, `articulo`, `producto`, `grupo_dane` | | Igual que arriba |
| `en_canasta` | booleano | Del catálogo |
| `semana_inicio` | fecha | Primer día de la semana |
| `anio`, `mes`, `periodo` | entero | Mes al que pertenece la semana |
| `precio`, `precio_min`, `precio_max` | decimal | Pesos por `unidad` |
| `unidad` | texto | `kg`, `unidad` o `litro` |

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
Una fila por eslabón, producto, departamento y rezago. Responde "¿qué tanto afecta el clima?".
Método y razones en `src/indicators/sensibilidad.py`. **Lo que cuenta como hallazgo es `q_valor < 0,1`**, no el p-valor solo.
| Columna | Tipo | Descripción |
|---|---|---|
| `eslabon` | texto | `oni->lluvia`, `lluvia->oferta`, `oferta->precio`, `lluvia->precio` |
| `producto`, `art_id` | | Producto del precio diario y su artículo de abastecimiento (solo si el nombre es idéntico); nulos en `oni->lluvia` |
| `departamento` | texto | |
| `variable` | texto | `lluvia`, `abastecimiento`, `oni` |
| `rezago_meses` | entero | 0 a 6 |
| `coeficiente` | decimal | Efecto estimado (signo = dirección) |
| `p_valor` | decimal | Significancia |
| `n` | entero | Meses usados |
| `q_valor` | decimal | p-valor corregido por pruebas múltiples (Benjamini-Hochberg, dentro de cada eslabón) |
| `metodo` | texto | `correlacion_pearson`, `regresion_estacional` o `panel_efectos_fijos` |

### `indicador_quiebres` (Chow y Brown-Forsythe)
Una fila por producto, fecha candidata (inicio de fase ENSO) y tipo de cambio. Método y las tres trampas que evita en `src/indicators/quiebres.py`.
| Columna | Tipo | Descripción |
|---|---|---|
| `producto`, `mercado` | texto | `mercado` = `nacional` (mediana de los mercados) |
| `periodo_quiebre`, `fase_que_empieza` | entero, texto | Fecha probada y fase ENSO que empieza ahí |
| `que_cambia` | texto | `ritmo` (Chow sobre el cambio mensual promedio) o `volatilidad` (Brown-Forsythe) |
| `f_chow`, `p_valor`, `q_valor` | decimal | Estadístico F, p y p corregido (Benjamini-Hochberg dentro de cada `que_cambia`) |
| `valor_antes_pct`, `valor_despues_pct` | decimal | % por mes: promedio del cambio (ritmo) o desviación estándar (volatilidad), del precio relativo a la canasta |
| `n_antes`, `n_despues` | entero | Meses usados en cada tramo |
| `hay_quiebre` | booleano | `q_valor < 0,1` |

### `pronostico_precio`
| Columna | Tipo | Descripción |
|---|---|---|
| `art_id`, `articulo`, `mercado` | | Siempre por artículo, nunca promedio de variedades |
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
| `config/catalogo_articulos.csv` | `art_id`, `articulo`, `producto`, `grupo_dane`, `unidad`, `distingue_por` (`variedad`/`calidad`/`presentacion`/`origen`/`procesado`/`unico`), `en_canasta`, `nota` | Parte de `data/openrefine/catalogo_sipsa_crudo.csv` (448 artículos, ya generado por Claude 1 con `unidad_sugerida`). OpenRefine **propone** `producto` con clustering y **una persona revisa** cada grupo contra las reglas de arriba. El JSON de operaciones va a `data/openrefine/` |
| `config/geo/colombia_departamentos.geojson` | propiedad `DPTO` = código DANE | Descarga verificada; documentar origen y licencia en `docs/fuentes_app.md` (archivo propio de Claude 2) |
