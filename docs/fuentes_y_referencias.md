# Fuentes de datos, APIs y referencias — Caso 8

Inventario de datos, no texto del informe: el informe lo redacta el equipo con sus propias palabras
(la guía AE2 considera plagio el texto copiado de una IA). Todo lo de abajo sale del código del
repo (`src/acquisition/`), de `docs/verificacion_api.md` o de una consulta hecha el **29-sep-2026**.

Leyenda de verificación: **[Crossref]** = autores, revista, volumen, páginas y DOI leídos de la API
pública de Crossref; **[API]** = leído de la API del propio portal; **[200]** = el enlace respondió
HTTP 200 pero no se leyó el título de la página (confírmenlo al citar).

---

## 1. Las 6 fuentes (y su papel en la guía AE2)

La guía pide mínimo 3 fuentes: una tipo **sensor**, un **archivo** (CSV/Excel) y una de **internet** (API o web).

| # | Fuente | Tipo según la guía | Acceso | Frecuencia | Módulo |
|---|---|---|---|---|---|
| 1 | SIPSA (DANE): precios mayoristas | Internet (API SOAP) | sin token | diaria | `sipsa.py` |
| 2 | IDEAM: lluvia (y temperatura) medida por estaciones | **Sensor** (API Socrata) | token opcional | 10 min (lluvia) / 1 h (temperatura) | `ideam.py` |
| 3 | FAOSTAT: producción, comercio, balances, precios | **Archivo** (ZIP con CSV) | sin token | anual | `faostat_bulk.py` |
| 4 | NASA POWER: clima por zona productora | Internet (API REST) | sin token | mensual y diaria | `nasa_power.py`, `nasa_power_diario.py` |
| 5 | ONI (NOAA CPC): El Niño / La Niña | Archivo de texto por URL | sin token | mensual | `oni.py` |
| 6 | Pink Sheet (Banco Mundial): fertilizantes y energía | **Archivo** (Excel) | sin token | mensual | `pink_sheet.py` |

## 2. Cada API en detalle

### 2.1 SIPSA — DANE (SOAP)
- **Endpoint (usar HTTPS):** `https://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService`
- **WSDL:** `http://appweb.dane.gov.co/sipsaWS/SrvSipsaUpraBeanService?WSDL` — el WSDL declara el endpoint por HTTP, pero **HTTP no procesa SOAP** (devuelve HTML); hay que llamar por HTTPS.
- **Protocolo:** SOAP 1.2, `Content-Type: application/soap+xml; charset=utf-8`, sin cabecera `SOAPAction`. Namespace `http://servicios.sipsa.co.gov.dane/`.
- **Método usado:** `promediosSipsaCiudad` (sin argumentos). Devuelve **todo el histórico** cada vez (~112 MB, idempotente). Otros métodos del WSDL: `promediosSipsaParcial`, `promediosSipsaSemanaMadr`, `promediosSipsaMesMadr`, `promedioAbasSipsaMesMadr`, `consultarInsumosSipsaMesMadr(arg0:int)`. Los `*Madr` no se usan (pueden filtrar por la bandera `enviado`).
- **Campos:** `ciudad`, `codProducto`, `producto`, `precioPromedio` (**COP por kg**, confirmado contra FAOSTAT), `fechaCaptura`, `fechaCreacion`, `enviado`, `regId`.
- **Trampas:** no hay datos de 2021-01 a 2022-01; CÚCUTA pasó a SAN JOSÉ DE CÚCUTA en dic. 2022.
- **Descarga del 29-sep-2026:** 387 063 registros.

### 2.2 IDEAM — datos.gov.co (API Socrata / SODA)
- **Base:** `https://www.datos.gov.co/resource/<id>.json`
- **Datasets** [API]: `s54a-sgyg` = "Precipitación" (mm, cada 10 min, ~165 M filas); `sbwg-7ju4` = "Temperatura Ambiente del Aire" (°C, cada hora). Ambos con atribución IDEAM, procedencia oficial. Fichas: `https://www.datos.gov.co/d/s54a-sgyg` y `https://www.datos.gov.co/d/sbwg-7ju4`.
- **Columnas:** `codigoestacion`, `codigosensor`, `fechaobservacion`, `valorobservado`, `nombreestacion`, `departamento`, `municipio`, `zonahidrografica`, `latitud`, `longitud`, `descripcionsensor`, `unidadmedida`.
- **Consulta (SoQL):** `$select`, `$where`, `$group`, `$order`, `$limit`, `$offset`. El proyecto agrega **en el servidor** y **un mes por llamada** (año/semestre/trimestre dan timeout). Aun así, dos meses de Cundinamarca (dic-2024 y ene-2025) dieron timeout con esa consulta: se resolvieron pidiendo ventanas de 5 días y combinando (sumas y conteos se suman; mínimo y máximo se recalculan). Antioquia no estaba descargada y se bajó con el mismo método.
- **Autenticación:** opcional, cabecera `X-App-Token` (variable `SOCRATA_APP_TOKEN`); sin token responde con límite de tasa.
- **Trampa importante:** cada departamento aparece con **dos convenciones de mayúsculas** (`BOYACÁ` y `Boyacá`) que se reparten el tiempo. Se piden ambas y la limpieza las unifica (`a_vocabulario_config`).
- **Sensores:** convencional (0240 lluvia / 0068 temperatura) y GPRS (0257 / 0071, lecturas cada ~2 min). Se agrupa por `codigosensor` para no sumar dos veces.
- **Estado:** lluvia descargada 2020–2026 para los 8 departamentos de zonas productoras (600 filas departamento-mes, 450 estaciones). **La temperatura (`sbwg-7ju4`) está verificada pero no se descargó**, y la app solo muestra lluvia.

### 2.3 FAOSTAT — descargas masivas (y API REST)
- **Índice:** `https://bulks-faostat.fao.org/production/datasets_E.xml` (campos `DatasetCode`, `DateUpdate`, `FileLocation`, `FileSize`).
- **Archivos usados** (`https://bulks-faostat.fao.org/production/…`):
  - PP `Prices_E_All_Data_(Normalized).zip` — precio al productor
  - QCL `Production_Crops_Livestock_E_All_Data_(Normalized).zip` — producción
  - TCL `Trade_CropsLivestock_E_All_Data_(Normalized).zip` — comercio
  - FBS `FoodBalanceSheets_E_All_Data_(Normalized).zip` — balances alimentarios
  - QV `Value_of_Production_E_All_Data_(Normalized).zip` — valor de la producción
  - PE `Exchange_rate_E_All_Data_(Normalized).zip` — tasa de cambio
- **API REST:** `https://faostatservices.fao.org/api/v1` → **401 sin token** (`Missing Authorization Header`). No se usa. `fenixservices.fao.org` ya no responde (521).
- **Portal:** `https://www.fao.org/faostat/en/#data` [200].

### 2.4 NASA POWER (REST, sin llave)
- **Mensual:** `https://power.larc.nasa.gov/api/temporal/monthly/point` — sirve años calendario completos; el límite lo publica en `.../monthly/configuration` (`settings.end`).
- **Diario:** `https://power.larc.nasa.gov/api/temporal/daily/point` (`start`/`end` en `AAAAMMDD`; los últimos ~3 días vienen en `-999`).
- **Parámetros:** `latitude`, `longitude`, `community=ag`, `parameters=PRECTOTCORR,T2M`, `format=JSON`, `start`, `end`. Centinela de dato faltante: `-999` (se lee de `header.fill_value`).
- **Limitación:** la celda de grilla promedia el relieve (a Villavicencio, 467 m reales, le asigna 1392 m). Por eso se usan **anomalías**, no valores absolutos.
- **Documentación:** `https://power.larc.nasa.gov/docs/services/api/` [200] y `https://power.larc.nasa.gov/docs/methodology/` [200].

### 2.5 ONI — NOAA CPC
- **Archivo:** `https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt` (ancho fijo, columnas `SEAS YR TOTAL ANOM`, desde DJF 1950). Umbral El Niño ≥ +0,5 °C. Los 3 últimos trimestres pueden revisarse.
- **Página:** `https://www.cpc.ncep.noaa.gov/products/analysis_monitoring/ensostuff/ONI_v5.php` [200].

### 2.6 Pink Sheet — Banco Mundial
- **Página:** `https://www.worldbank.org/en/research/commodity-markets` [200]. El enlace al Excel **se descubre al ejecutar** (cambia con cada edición). Último usado: `https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx`, hoja `Monthly Prices`.

## 3. Estado de los datos (29-sep-2026)

| Fuente | Último dato en la base |
|---|---|
| SIPSA | septiembre de 2026 (descarga del 29-sep; el mes está abierto) |
| IDEAM lluvia | septiembre de 2026 (Quindío llega a julio) |
| NASA POWER | mensual hasta julio de 2026, diario hasta pocos días antes de la consulta |
| ONI | JJA 2026 |
| FAOSTAT | depende del dominio: PP 2026-01-09, QCL 2025-12-31, TCL 2026-07-24, FBS 2025-10-28, QV 2026-05-11, PE 2026-05-29 (fechas de actualización de FAO al 11-sep-2026) |

## 4. Referencias en IEEE

### Académicas (10) — todas verificadas en Crossref

[1] H. D. Mafukidze, A. Nechibvute, A. Yahya, I. A. Badruddin, S. Kamangar, and M. Hussien, "Development of a modularized undergraduate data science and big data curricular using no-code software development tools," *IEEE Access*, vol. 12, pp. 100939–100956, 2024, doi: 10.1109/ACCESS.2024.3429241.

[2] L. F. Melo-Velandia, C. A. Orozco-Vanegas, and D. Parra-Amado, "Extreme weather events and high Colombian food prices: A non-stationary extreme value approach," *Agric. Econ.*, vol. 53, no. S1, pp. 21–40, 2022, doi: 10.1111/agec.12753.

[3] A. Bastianin, A. Lanza, and M. Manera, "Economic impacts of El Niño southern oscillation: Evidence from the Colombian coffee market," *Agric. Econ.*, vol. 49, no. 5, pp. 623–633, 2018, doi: 10.1111/agec.12447.

[4] M. K. Mohanty, P. K. Guha Thakurta, and S. Kar, "Agricultural commodity price prediction model: A machine learning framework," *Neural Comput. Appl.*, vol. 35, no. 20, pp. 15109–15128, 2023, doi: 10.1007/s00521-023-08528-7.

[5] C. L. Gilbert and C. W. Morgan, "Food price volatility," *Phil. Trans. R. Soc. B*, vol. 365, no. 1554, pp. 3023–3034, 2010, doi: 10.1098/rstb.2010.0139.

[6] H. Aboelkhair, M. Morsy, and G. El Afandi, "Assessment of agroclimatology NASA POWER reanalysis datasets for temperature types and relative humidity at 2 m against ground observations over Egypt," *Adv. Space Res.*, vol. 64, no. 1, pp. 129–142, 2019, doi: 10.1016/j.asr.2019.03.032.

[7] K. E. Trenberth, "The definition of El Niño," *Bull. Amer. Meteor. Soc.*, vol. 78, no. 12, pp. 2771–2777, 1997, doi: 10.1175/1520-0477(1997)078<2771:TDOENO>2.0.CO;2.

[8] A. Sparks, "nasapower: A NASA POWER global meteorology, surface solar energy and climatology data client for R," *J. Open Source Softw.*, vol. 3, no. 30, Art. no. 1035, 2018, doi: 10.21105/joss.01035.

[9] M. Raasveldt and H. Mühleisen, "DuckDB: An embeddable analytical database," in *Proc. 2019 Int. Conf. Manage. Data (SIGMOD)*, Amsterdam, The Netherlands, 2019, pp. 1981–1984, doi: 10.1145/3299869.3320212.

[10] H. Wickham, "Tidy data," *J. Stat. Softw.*, vol. 59, no. 10, 2014, doi: 10.18637/jss.v059.i10.

*Nota:* el lugar y la ciudad de [9] no vienen en Crossref; si lo quieren en el formato completo, verifíquenlo en la página de ACM.

### Técnicas y oficiales

[11] Food and Agriculture Organization of the United Nations, "FAOSTAT," FAO. [Online]. Available: https://www.fao.org/faostat/en/#data. [Accessed: Sep. 29, 2026]. **[200]**

[12] Departamento Administrativo Nacional de Estadística (DANE), "Sistema de información de precios y abastecimiento del sector agropecuario (SIPSA)." [Online]. Available: https://www.dane.gov.co/index.php/estadisticas-por-tema/agropecuario/sistema-de-informacion-de-precios-sipsa. [Accessed: Sep. 29, 2026]. **[200]**

[13] Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM), "Precipitación," Datos Abiertos Colombia, dataset s54a-sgyg. [Online]. Available: https://www.datos.gov.co/d/s54a-sgyg. [Accessed: Sep. 29, 2026]. **[API]**

[14] IDEAM, "Temperatura ambiente del aire," Datos Abiertos Colombia, dataset sbwg-7ju4. [Online]. Available: https://www.datos.gov.co/d/sbwg-7ju4. [Accessed: Sep. 29, 2026]. **[API]**

[15] NASA, "Prediction Of Worldwide Energy Resources (POWER) — API documentation." [Online]. Available: https://power.larc.nasa.gov/docs/services/api/. [Accessed: Sep. 29, 2026]. **[200]**

[16] NOAA Climate Prediction Center, "Oceanic Niño Index (ONI)," data file oni.ascii.txt. [Online]. Available: https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt. [Accessed: Sep. 29, 2026]. **[200]**

[17] World Bank, "Commodity markets (Pink Sheet)." [Online]. Available: https://www.worldbank.org/en/research/commodity-markets. [Accessed: Sep. 29, 2026]. **[200]**

[18] OpenRefine, "OpenRefine documentation." [Online]. Available: https://docs.openrefine.org/. [Accessed: Sep. 29, 2026]. **[200]**

Total: **18** (10 académicas, 8 técnicas). La guía pide 10 en total y 5 académicas; solo cuentan las que **citen en el texto**.

## 5. Para qué sirve cada académica (datos de los resúmenes; redáctenlo ustedes)

| Ref. | Qué aporta al proyecto |
|---|---|
| [2] | En Colombia (1985–2020), los alimentos perecederos son más vulnerables a eventos climáticos extremos; la poca lluvia empuja los precios altos. Justifica cruzar clima con precios. |
| [3] | Efecto de El Niño/La Niña sobre producción, exportaciones y precio del café colombiano; el efecto es modesto. Justifica usar el ONI y advierte no exagerar su peso. |
| [4] | Marco de aprendizaje automático para predecir precios de commodities agrícolas. Trabajo relacionado sobre predicción. |
| [5] | Explica qué es la volatilidad de precios de alimentos y por qué importa. Marco conceptual del reto. |
| [6] | Evalúa NASA POWER contra estaciones en tierra (Egipto): aceptable en temperatura, con más error en humedad. Respalda usar POWER con cautela. |
| [7] | Definición de El Niño que sustenta el índice ONI. |
| [8] | Cliente de datos de NASA POWER: describe qué parámetros ofrece la API. |
| [9] | Motor DuckDB de la base analítica. |
| [10] | Formato "tidy" de las tablas (una fila por observación): base de la limpieza. |
| [1] | Referencia del propio caso (aprendizaje por proyectos con herramientas no-code de ciencia de datos). |

## 6. No verificado: no lo citen sin comprobarlo

Para la parte de DAQ (muestreo y cuantificación) suelen citarse el teorema de Nyquist–Shannon
(Shannon, *Proc. IRE*, 1949) y el manual de la OMM **WMO-No. 8** (que ya menciona
`verificacion_api.md`). No pude confirmar sus datos bibliográficos desde aquí; búsquenlos en la base
de datos de la biblioteca del ITM y confirmen autores, volumen y páginas.
