# Verificación de fuentes — Fase 0

Fecha de las pruebas: **2026-09-11**. Todas las pruebas se corrieron desde Colombia con los
scripts `scripts/probe_faostat_api.py` y `scripts/probe_fuentes.py`. La evidencia cruda queda
en `data/raw/_probe/` (no versionada).

---

## 1. FAOSTAT — API REST

| URL base probada | Ruta | Sin token |
|---|---|---|
| `https://faostatservices.fao.org/api/v1` | `/en/groups`, `/en/domains`, `/en/data/PP?...` | **401** — cuerpo: `Missing Authorization Header` |
| `https://fenixservices.fao.org/faostat/api/v1` | las mismas | **521** (Cloudflare: servidor origen caído) |

**Conclusión:** la URL base válida es `https://faostatservices.fao.org/api/v1` y **exige token**.
La ficha de api-evangelist que decía "no requiere autenticación" está desactualizada, y
`fenixservices` ya no responde. El token se obtiene en el Developer Portal de FAO
(<https://www.fao.org/faostat/en/#developer-portal>).

**Pendiente:** no hay token en el entorno, así que no se pudo verificar el formato exacto de la
cabecera (`Authorization: Bearer <token>` vs. parámetro de consulta), ni las rutas reales, ni el
límite de 2 peticiones/segundo que reporta el cliente comunitario. `# TODO VERIFICAR` una vez
cargado `FAOSTAT_API_KEY`.

**Mitigación:** la API REST solo se necesita para actualizaciones incrementales. La carga
histórica completa sale de las descargas masivas, que sí funcionan sin credenciales.

---

## 2. FAOSTAT — Descargas masivas ✅

`https://bulks-faostat.fao.org/production/datasets_E.xml` → 200, 117 KB, 69 datasets.

Campos reales de cada `<Dataset>`: `DatasetCode`, `DatasetName`, `Topic`, `DatasetDescription`,
`Contact`, `Email`, **`DateUpdate`**, `CompressionFormat`, `FileType`, **`FileSize`**,
`FileRows`, **`FileLocation`**.

El campo de fecha de actualización es `DateUpdate` (formato `2026-04-30T00:00:00`) y la URL de
descarga es `FileLocation`. Esos dos campos son los que usa el detector de datos nuevos.

Estado de los seis dominios que nos interesan:

| Código | Nombre | Última actualización | Tamaño |
|---|---|---|---|
| PP | Prices: Producer Prices | 2026-01-09 | 11 411 KB |
| QCL | Production: Crops and livestock products | 2025-12-31 | 33 127 KB |
| TCL | Trade: Crops and livestock products | 2026-07-24 | 267 104 KB |
| FBS | Food Balances (2010-) | 2025-10-28 | 53 556 KB |
| QV | Value of Agricultural Production | 2026-05-11 | 29 616 KB |
| PE | Prices: Exchange rates | 2026-05-29 | 1 171 KB |

Los tamaños coinciden con los documentados en `CLAUDE.md`.

---

## 3. SIPSA (DANE) — SOAP ✅ con dos correcciones importantes

### 3.1 El endpoint es HTTPS, no HTTP

La guía del DANE de 2020 y el propio WSDL declaran la dirección
`http://appweb.dane.gov.co:80/sipsaWS/SrvSipsaUpraBeanService`. Ese endpoint por HTTP
**no procesa SOAP**: responde 200 con la página HTML informativa de JAX-WS, tanto con SOAP 1.1
como con SOAP 1.2. Por eso `zeep` falla con
`XMLSyntaxError: The root element found is html`.

El mismo servicio **por HTTPS sí responde SOAP correctamente**:

```
https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService
```

El WSDL para descubrimiento sigue estando en HTTP; hay que sobreescribir la dirección del
transporte antes de invocar.

### 3.2 El binding es SOAP 1.2

El WSDL declara `<soap12:binding transport="http://www.w3.org/2003/05/soap/bindings/HTTP/">`.
Content-Type correcto: `application/soap+xml; charset=utf-8`. No lleva cabecera `SOAPAction`.

### 3.3 Métodos reales (leídos del WSDL, no de la guía)

| Método | Argumentos |
|---|---|
| `consultarInsumosSipsaMesMadr` | `arg0: xsd:int` |
| `promedioAbasSipsaMesMadr` | ninguno |
| `promediosSipsaCiudad` | ninguno |
| `promediosSipsaMesMadr` | ninguno |
| `promediosSipsaParcial` | ninguno |
| `promediosSipsaSemanaMadr` | ninguno |

Los seis coinciden con los que lista la guía de 2020.

### 3.4 Prueba en vivo de `promediosSipsaCiudad`

Se llamó **dos veces**. Ambas devolvieron exactamente **112 265 566 bytes** y **383 545**
registros `<return>`.

**Conclusión:** `promediosSipsaCiudad` devuelve el histórico completo y es idempotente. La
bandera `enviado` existe en la respuesta pero viene en `0`, o sea que este método **no** filtra
por registros ya consultados.

Estructura real de un registro:

```xml
<return>
  <ciudad>MANIZALES</ciudad>
  <codProducto>16</codProducto>
  <enviado>0</enviado>
  <fechaCaptura>2026-09-10T00:00:00-05:00</fechaCaptura>
  <fechaCreacion>2026-09-11T12:00:01-05:00</fechaCreacion>
  <precioPromedio>3500</precioPromedio>
  <producto>Guayaba*</producto>
  <regId>694559</regId>
</return>
```

`precioPromedio` es **precio en COP por kilogramo**, no una cantidad: 3 500 COP/kg de guayaba y
1 800 COP/kg de limón Tahití son valores coherentes con el mercado mayorista.

### Confirmación de la unidad por triangulación (hallada en Fase 3) ✅

La duda quedó cerrada comparando contra FAOSTAT, que publica el precio al productor en COP por
tonelada. Dividiendo por mil y contrastando contra el promedio anual de SIPSA:

| Producto | Año | FAOSTAT (COP/kg) | SIPSA (COP/kg) | Diferencia |
|---|---:|---:|---:|---:|
| Papa | 2022 | 1 964,7 | 2 012 | 2,4 % |
| Tomate | 2022 | 2 661,7 | 2 657 | 0,2 % |
| Tomate | 2023 | 2 991,3 | 2 897 | 3,2 % |
| Aguacate | 2023 | 7 854,0 | 6 845 | 14,7 % |

Dos fuentes que caen dentro del 3 % en varios productos y años **confirman que
`precioPromedio` es COP por kilogramo**. La unidad ya no es un supuesto.

### Pero ese mismo resultado abre una pregunta que hay que decir en el reporte ⚠️

Un precio mayorista debería estar **por encima** de un precio al productor: entre los dos hay
transporte, acopio e intermediación. Acá son casi iguales.

Los 6 893 registros de precio al productor de Colombia llevan flag `A`, "Official figure", o
sea que FAO los recibe del gobierno colombiano. Lo más probable es que ambas series salgan del
mismo sistema de captura del DANE.

**Consecuencia:** para precios, SIPSA y FAOSTAT **no son fuentes independientes**. Calcular un
"margen de intermediación" restando una de la otra no mide intermediación, mide la diferencia
entre dos agregaciones del mismo dato. No se debe presentar como margen.

Esto no invalida el cruce: sirve como validación cruzada de unidades y de consistencia, que es
justamente para lo que se usa acá.

Dato más reciente disponible: `fechaCaptura = 2026-09-10` (el día anterior a la prueba), lo que
confirma la actualización diaria.

**No probado a propósito:** los métodos `*Madr`, porque son los candidatos a traer solo registros
no enviados antes. No se llaman hasta que la Fase 1 tenga la persistencia lista, para no quemar
datos irrecuperables.

---

## 4. NASA POWER ✅

OpenAPI: `https://power.larc.nasa.gov/api/temporal/monthly/openapi.json` → 200.

Parámetros obligatorios de `/api/temporal/monthly/point`: `start`, `end`, `latitude`,
`longitude`, `community`, `parameters`. Opcionales: `format`, `units`, `user`, `header`,
`time-standard`, `site-elevation`, `wind-elevation`, `wind-surface`. También existe el endpoint
`/regional` con caja de coordenadas.

Consulta real verificada (Bogotá, 2024–2025, comunidad `ag`):

```
https://power.larc.nasa.gov/api/temporal/monthly/point
  ?start=2024&end=2025&latitude=4.65&longitude=-74.1
  &community=ag&parameters=PRECTOTCORR,T2M&format=JSON
```

Respondió 200 sin llave. Los valores llegan en `properties.parameter.<PARAM>` con claves
`AAAAMM`, por ejemplo `{"202401": 0.62, "202402": 2.34}`. Los nombres de parámetro
`PRECTOTCORR` (precipitación corregida) y `T2M` (temperatura a 2 m) están confirmados.

### Corrección al supuesto de "meses cerrados" (hallada en Fase 1)

El `CLAUDE.md` asumía que bastaba con pedir hasta el último mes cerrado, porque POWER publica
con dos o tres días de rezago. **Eso vale para el endpoint diario, no para el mensual.**

Pedir `start=2026&end=2026` en septiembre de 2026 devuelve **422** con este mensaje:

```
Please provide a correct end date. Your end date out of range.
The data is available to 2025/12/31.
```

O sea que el endpoint mensual sirve solo **años calendario completos** y va con más de un año
de rezago. El límite no hay que estimarlo: el propio servicio lo publica en
`https://power.larc.nasa.gov/api/temporal/monthly/configuration`, en `settings.end`
(`2025-12-31T00:00:00` al momento de la prueba). El módulo lo lee de ahí.

Otros dos detalles confirmados contra la respuesta real:

- Cada año trae una clave extra `<anio>13` con el promedio anual del parámetro. No es un mes y
  se descarta.
- El valor centinela de dato faltante viene declarado en `header.fill_value` (`-999.0`). Se lee
  del encabezado en vez de dejarlo fijo en el código.

### Limitación de la grilla en terreno montañoso (hallada en Fase 2)

POWER devuelve, junto con cada consulta, la elevación que asigna a la celda de grilla. En
Colombia esa elevación difiere fuerte de la real, porque la celda promedia el relieve:

| Zona consultada | Elevación real aproximada | Elevación que asigna POWER | Temperatura media |
|---|---:|---:|---:|
| Villavicencio, Meta | 467 m | 1 392 m | 18,95 °C |
| Bogotá, Cundinamarca | 2 640 m | 1 790 m | 18,63 °C |
| Medellín, Antioquia | 1 495 m | 2 074 m | 16,37 °C |

O sea que la serie climática **no es el clima del municipio**, es el promedio de una celda que
mezcla valle y montaña. Para Villavicencio eso subestima la temperatura en varios grados.

Consecuencias prácticas, que deben quedar dichas en el reporte:

- Las temperaturas absolutas no sirven para caracterizar la zona productora.
- Las **anomalías** sí sirven, porque comparan cada mes contra el promedio histórico del mismo
  mes en la misma celda, y el sesgo de elevación se cancela.
- Por eso el indicador de contexto climático usa la anomalía de precipitación, no el valor
  absoluto.

La elevación que reporta POWER se conserva como columna `elevacion_grilla_m` en la tabla de
clima, para que la limitación sea visible en los datos y no solo en este documento.

---

## 5. ONI — NOAA CPC ✅

`https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` → 200, 23 KB.

Formato de ancho fijo con encabezado `SEAS  YR   TOTAL   ANOM`, desde `DJF 1950`. Último
trimestre disponible: **`JJA 2026`, anomalía +1.80 °C**, o sea El Niño en curso (umbral ≥ +0.5).
Los tres últimos trimestres pueden revisarse después, así que se marcan como estimados.

**Pendiente:** confirmar si el CPC pasó a usar el Relative ONI (RONI) como índice oficial de
verificación. La serie ONI clásica sigue publicándose en esta URL.

---

## 6. Pink Sheet — Banco Mundial ✅

`https://www.worldbank.org/en/research/commodity-markets` → 200, 55 KB de HTML. La página
responde; la URL del Excel mensual hay que descubrirla desde el HTML en tiempo de ejecución, no
escribirla a mano.

---

## Resumen

| Fuente | Estado | Bloqueante |
|---|---|---|
| FAOSTAT bulk | ✅ funciona | no |
| FAOSTAT API REST | ⚠️ exige token | sí, para actualización incremental |
| SIPSA SOAP | ✅ funciona por HTTPS + SOAP 1.2 | no |
| NASA POWER | ✅ funciona | no |
| ONI | ✅ funciona | no |
| Pink Sheet | ✅ página responde | no |

Solo una cosa bloquea el avance: el token de FAOSTAT.
