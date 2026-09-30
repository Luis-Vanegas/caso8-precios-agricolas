# Guía de Power Query — integración

Power Query es el tercer entregable obligatorio, junto con Python y OpenRefine. Este paso lo
ejecutás vos en Excel.

**Aclaración honesta:** el código M de `powerquery/` está escrito pero **no fue ejecutado**, porque
no tengo Excel. Para que puedas verificarlo, la misma lógica está implementada en SQL y su
resultado está en `data/interim/base_integrada_referencia.csv`. Si tu Power Query da las mismas
cifras que la sección "Resultado esperado", quedó bien.

---

## Qué produce

Una tabla de 33.949 filas y 18 columnas: cada precio mayorista mensual con su contexto de
precio al productor, fase El Niño y anomalía de lluvia en la zona productora.

## Orden de las consultas

Las consultas se referencian entre sí, así que hay que crearlas en este orden:

| # | Consulta | Archivo | Depende de |
|---|---|---|---|
| 0 | `CarpetaProyecto` (parámetro) | `00_Parametros.pq` | — |
| 1 | `SipsaMensual` | `01_SipsaMensual.pq` | parámetro |
| 2 | `FaostatPrecioProductor` | `02_FaostatPrecioProductor.pq` | parámetro |
| 3 | `Enso` | `04_Enso.pq` | parámetro |
| 4 | `Clima` | `05_Clima.pq` | parámetro |
| 5 | `ZonasPuente` | `06_ZonasPuente.pq` | parámetro |
| 6 | `BaseIntegrada` | `03_BaseIntegrada.pq` | las cinco anteriores |

El nombre de cada consulta en Excel debe ser **exactamente** el de la columna "Consulta". El
código M las llama por ese nombre.

## Pasos

1. Abrí Excel en un libro nuevo. Guardalo como `powerquery/integracion.xlsx`.
2. `Datos` → `Obtener datos` → `Iniciar el editor de Power Query`.
3. `Inicio` → `Administrar parámetros` → `Nuevo parámetro`. Nombre `CarpetaProyecto`, tipo Texto,
   valor la ruta de tu proyecto. Es lo único que cambia al mover el proyecto de máquina.
4. Para cada consulta, en ese orden: `Inicio` → `Nueva consulta` → `Consulta nula`, luego
   `Editor avanzado`, pegá el contenido del `.pq` y renombrá la consulta.
5. En `BaseIntegrada`, `Inicio` → `Cerrar y cargar en...` → `Tabla` en una hoja nueva.
6. Las cinco consultas intermedias: clic derecho → desmarcá `Habilitar carga`. No hace falta
   materializarlas, solo alimentan a la última.

## Resultado esperado

Compará estas cifras con las tuyas:

| Verificación | Valor esperado |
|---|---:|
| Filas totales | 33 949 |
| Columnas | 18 |
| Filas con precio al productor | 14 106 |
| Filas con razón calculada | 8 924 |
| Filas con fase ENSO | 32 974 |
| Filas con anomalía de lluvia | 5 922 |
| Mediana de la razón mayorista/productor | 0,838 |

Nota (22 sep. 2026): al unificar el mercado de Cúcuta las filas pasaron de 33 977 a 33 949. Los demás
conteos de esta tabla se calcularon antes de ese cambio y pueden variar en unas decenas.

Si te da distinto, mirá primero estas tres causas, que son las que fallan siempre.

## Los tres errores que hay que evitar

### 1. La codificación

Los CSV vienen en UTF-8 con BOM. En `Csv.Document` va `Encoding = 65001`, que es UTF-8. Si lo
dejás en el valor por defecto, Excel lee `Limón` como `LimÃ³n` y las uniones por nombre de
producto dejan de encontrar filas.

**Cómo lo detectás:** mirá la columna `producto` y buscá `Plátano hartón verde`. Si ves
caracteres raros, la codificación está mal.

### 2. Las unidades

FAOSTAT publica el precio al productor en **pesos por tonelada**. SIPSA está en **pesos por
kilogramo**. La consulta `FaostatPrecioProductor` divide por mil.

Si te salteás esa división, la razón entre los dos precios da alrededor de 0,0008 en vez de
0,838. Es un error de mil veces que igual produce un gráfico con aspecto normal.

### 3. El cruce del clima va por el puente

Esta la cometí yo y quiero que la veas.

Mi primera versión unía `clima` con SIPSA directamente por `producto`. El código estaba bien
escrito, corría sin ningún error, y unía **cero filas de 33.949**. ¿Por qué? Porque la
configuración de zonas dice `Papa` y SIPSA dice `Papa negra*`. Nunca iban a coincidir.

**Un join que no encuentra nada no se queja.** Devuelve nulos y sigue de largo. Por eso la
unión va por `ZonasPuente`, que traduce entre los dos vocabularios.

**Cómo lo detectás:** contá las filas con `precipitacion_anomalia` no nula. Si te da 0, el
cruce está roto. Deben ser 5.922.

## Lo que esta base NO permite concluir

La columna `razon_mayorista_productor` **no es un margen de intermediación**, y presentarla como
tal sería un error grave.

Los 6.893 registros de precio al productor de Colombia en FAOSTAT llevan el flag `A`, "cifra
oficial", o sea que FAO los recibe del gobierno colombiano. Lo más probable es que salgan del
mismo sistema de captura del DANE que alimenta SIPSA. Para precios, las dos fuentes **no son
independientes**: restar una de la otra no mide intermediación, mide la diferencia entre dos
agregaciones del mismo dato.

La razón sirve como **validación cruzada de unidades y consistencia**, que es para lo que se usa
acá. Detalle completo en `docs/verificacion_api.md`.

## Al actualizar los datos

Corré en orden y después `Datos` → `Actualizar todo` en Excel:

```bash
.venv/Scripts/python.exe scripts/actualizar.py
.venv/Scripts/python.exe scripts/preparar.py
.venv/Scripts/python.exe scripts/integrar.py
```

Las rutas de los CSV no cambian, así que Power Query se refresca sin tocar nada.

**Importante:** cerrá la app de Streamlit antes de correr `actualizar.py`. La app mantiene el
archivo DuckDB abierto y en Windows eso bloquea la escritura.
