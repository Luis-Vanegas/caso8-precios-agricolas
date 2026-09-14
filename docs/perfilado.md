# Perfilado de las tablas limpias

Generado por `scripts/preparar.py`. Una fila por columna de cada tabla.

## Resumen por tabla

| tabla | filas | columnas | duplicados por clave |
|---|---:|---:|---:|
| faostat_pp | 13,489 | 17 | 0 |
| faostat_qcl | 21,346 | 16 | 0 |
| faostat_tcl | 79,395 | 16 | 0 |
| faostat_fbs | 24,399 | 16 | 0 |
| faostat_qv | 20,820 | 15 | 0 |
| faostat_pe | 511 | 16 | 0 |
| sipsa_diario | 383,718 | 11 | 0 |
| sipsa_mensual | 33,977 | 13 | 0 |
| clima | 2,520 | 10 | 0 |
| enso | 919 | 6 | 0 |
| insumos | 56,800 | 5 | 0 |

## Columnas

| tabla         | columna              | tipo                |   filas |   nulos |   pct_nulos |   unicos |     minimo |           maximo |
|:--------------|:---------------------|:--------------------|--------:|--------:|------------:|---------:|-----------:|-----------------:|
| faostat_pp    | area_codigo          | int64               |   13489 |       0 |        0    |        1 |     44     |     44           |
| faostat_pp    | area_m49             | str                 |   13489 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pp    | area                 | str                 |   13489 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pp    | item_codigo          | int64               |   13489 |       0 |        0    |      106 |     15     |   2051           |
| faostat_pp    | item_cpc             | str                 |   13489 |       0 |        0    |      106 |    nan     |    nan           |
| faostat_pp    | item                 | str                 |   13489 |       0 |        0    |      106 |    nan     |    nan           |
| faostat_pp    | elemento_codigo      | int64               |   13489 |       0 |        0    |        4 |   5530     |   5539           |
| faostat_pp    | elemento             | str                 |   13489 |       0 |        0    |        4 |    nan     |    nan           |
| faostat_pp    | anio_codigo          | int64               |   13489 |       0 |        0    |       35 |   1991     |   2025           |
| faostat_pp    | anio                 | Int64               |   13489 |       0 |        0    |       35 |   1991     |   2025           |
| faostat_pp    | mes_codigo           | int64               |   13489 |       0 |        0    |       13 |   7001     |   7021           |
| faostat_pp    | mes_nombre           | str                 |   13489 |       0 |        0    |       13 |    nan     |    nan           |
| faostat_pp    | unidad               | str                 |   13489 |    3546 |       26.29 |        3 |    nan     |    nan           |
| faostat_pp    | valor                | float64             |   13489 |       0 |        0    |    10236 |      1.6   |      4.23376e+07 |
| faostat_pp    | flag                 | str                 |   13489 |       0 |        0    |        2 |    nan     |    nan           |
| faostat_pp    | dominio              | str                 |   13489 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pp    | frecuencia           | str                 |   13489 |       0 |        0    |        2 |    nan     |    nan           |
| faostat_qcl   | area_codigo          | int64               |   21346 |       0 |        0    |        1 |     44     |     44           |
| faostat_qcl   | area_m49             | str                 |   21346 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_qcl   | area                 | str                 |   21346 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_qcl   | item_codigo          | int64               |   21346 |       0 |        0    |      168 |     15     |  17530           |
| faostat_qcl   | item_cpc             | str                 |   21346 |       0 |        0    |      168 |    nan     |    nan           |
| faostat_qcl   | item                 | str                 |   21346 |       0 |        0    |      168 |    nan     |    nan           |
| faostat_qcl   | elemento_codigo      | int64               |   21346 |       0 |        0    |       14 |   5111     |   5513           |
| faostat_qcl   | elemento             | str                 |   21346 |       0 |        0    |        8 |    nan     |    nan           |
| faostat_qcl   | anio_codigo          | int64               |   21346 |       0 |        0    |       64 |   1961     |   2024           |
| faostat_qcl   | anio                 | Int64               |   21346 |       0 |        0    |       64 |   1961     |   2024           |
| faostat_qcl   | unidad               | str                 |   21346 |       0 |        0    |       10 |    nan     |    nan           |
| faostat_qcl   | valor                | float64             |   21346 |     878 |        4.11 |    13589 |      0     |      4.06869e+07 |
| faostat_qcl   | flag                 | str                 |   21346 |       0 |        0    |        5 |    nan     |    nan           |
| faostat_qcl   | nota                 | object              |   21346 |   20796 |       97.42 |        1 |    nan     |    nan           |
| faostat_qcl   | dominio              | str                 |   21346 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_qcl   | frecuencia           | str                 |   21346 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_tcl   | area_codigo          | int64               |   79395 |       0 |        0    |        1 |     44     |     44           |
| faostat_tcl   | area_m49             | str                 |   79395 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_tcl   | area                 | str                 |   79395 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_tcl   | item_codigo          | int64               |   79395 |       0 |        0    |      444 |     10     |   2076           |
| faostat_tcl   | item_cpc             | str                 |   79395 |       0 |        0    |      444 |    nan     |    nan           |
| faostat_tcl   | item                 | str                 |   79395 |       0 |        0    |      444 |    nan     |    nan           |
| faostat_tcl   | elemento_codigo      | int64               |   79395 |       0 |        0    |        8 |   5608     |   5922           |
| faostat_tcl   | elemento             | str                 |   79395 |       0 |        0    |        4 |    nan     |    nan           |
| faostat_tcl   | anio_codigo          | int64               |   79395 |       0 |        0    |       64 |   1961     |   2024           |
| faostat_tcl   | anio                 | Int64               |   79395 |       0 |        0    |       64 |   1961     |   2024           |
| faostat_tcl   | unidad               | str                 |   79395 |       0 |        0    |        4 |    nan     |    nan           |
| faostat_tcl   | valor                | float64             |   79395 |       0 |        0    |    20847 |      0     |      7.74134e+07 |
| faostat_tcl   | flag                 | str                 |   79395 |       0 |        0    |        4 |    nan     |    nan           |
| faostat_tcl   | nota                 | object              |   79395 |   77032 |       97.02 |        1 |    nan     |    nan           |
| faostat_tcl   | dominio              | str                 |   79395 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_tcl   | frecuencia           | str                 |   79395 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_fbs   | area_codigo          | int64               |   24399 |       0 |        0    |        1 |     44     |     44           |
| faostat_fbs   | area_m49             | str                 |   24399 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_fbs   | area                 | str                 |   24399 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_fbs   | item_codigo          | int64               |   24399 |       0 |        0    |      122 |   2501     |   2961           |
| faostat_fbs   | item_fbs             | str                 |   24399 |       0 |        0    |      122 |    nan     |    nan           |
| faostat_fbs   | item                 | str                 |   24399 |       0 |        0    |      119 |    nan     |    nan           |
| faostat_fbs   | elemento_codigo      | int64               |   24399 |       0 |        0    |       20 |    511     |   5911           |
| faostat_fbs   | elemento             | str                 |   24399 |       0 |        0    |       20 |    nan     |    nan           |
| faostat_fbs   | anio_codigo          | int64               |   24399 |       0 |        0    |       14 |   2010     |   2023           |
| faostat_fbs   | anio                 | Int64               |   24399 |       0 |        0    |       14 |   2010     |   2023           |
| faostat_fbs   | unidad               | str                 |   24399 |       0 |        0    |        7 |    nan     |    nan           |
| faostat_fbs   | valor                | float64             |   24399 |       0 |        0    |     7471 |  -4737     |      5.97041e+07 |
| faostat_fbs   | flag                 | str                 |   24399 |       0 |        0    |        3 |    nan     |    nan           |
| faostat_fbs   | nota                 | float64             |   24399 |   24399 |      100    |        0 |    nan     |    nan           |
| faostat_fbs   | dominio              | str                 |   24399 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_fbs   | frecuencia           | str                 |   24399 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_qv    | area_codigo          | int64               |   20820 |       0 |        0    |        1 |     44     |     44           |
| faostat_qv    | area_m49             | str                 |   20820 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_qv    | area                 | str                 |   20820 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_qv    | item_codigo          | int64               |   20820 |       0 |        0    |      106 |     15     |   2057           |
| faostat_qv    | item_cpc             | str                 |   20820 |       0 |        0    |      106 |    nan     |    nan           |
| faostat_qv    | item                 | str                 |   20820 |       0 |        0    |      106 |    nan     |    nan           |
| faostat_qv    | elemento_codigo      | int64               |   20820 |       0 |        0    |        5 |     55     |    152           |
| faostat_qv    | elemento             | str                 |   20820 |       0 |        0    |        5 |    nan     |    nan           |
| faostat_qv    | anio_codigo          | int64               |   20820 |       0 |        0    |       64 |   1961     |   2024           |
| faostat_qv    | anio                 | Int64               |   20820 |       0 |        0    |       64 |   1961     |   2024           |
| faostat_qv    | unidad               | str                 |   20820 |       0 |        0    |        3 |    nan     |    nan           |
| faostat_qv    | valor                | float64             |   20820 |       0 |        0    |    18860 |      3     |      2.14323e+11 |
| faostat_qv    | flag                 | str                 |   20820 |       0 |        0    |        2 |    nan     |    nan           |
| faostat_qv    | dominio              | str                 |   20820 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_qv    | frecuencia           | str                 |   20820 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pe    | area_codigo          | int64               |     511 |       0 |        0    |        1 |     44     |     44           |
| faostat_pe    | area_m49             | str                 |     511 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pe    | area                 | str                 |     511 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pe    | elemento_codigo      | str                 |     511 |       0 |        0    |        2 |    nan     |    nan           |
| faostat_pe    | elemento             | str                 |     511 |       0 |        0    |        2 |    nan     |    nan           |
| faostat_pe    | moneda_iso           | str                 |     511 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pe    | moneda               | str                 |     511 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pe    | anio_codigo          | int64               |     511 |       0 |        0    |       57 |   1970     |   2026           |
| faostat_pe    | anio                 | Int64               |     511 |       0 |        0    |       57 |   1970     |   2026           |
| faostat_pe    | mes_codigo           | int64               |     511 |       0 |        0    |       13 |   7001     |   7021           |
| faostat_pe    | mes_nombre           | str                 |     511 |       0 |        0    |       13 |    nan     |    nan           |
| faostat_pe    | unidad               | float64             |     511 |     511 |      100    |        0 |    nan     |    nan           |
| faostat_pe    | valor                | float64             |     511 |       0 |        0    |      453 |     17.9   |   4922.3         |
| faostat_pe    | flag                 | str                 |     511 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pe    | dominio              | str                 |     511 |       0 |        0    |        1 |    nan     |    nan           |
| faostat_pe    | frecuencia           | str                 |     511 |       0 |        0    |        2 |    nan     |    nan           |
| sipsa_diario  | mercado              | str                 |  383718 |       0 |        0    |       21 |            |                  |
| sipsa_diario  | producto_codigo      | Int64               |  383718 |       0 |        0    |       33 |      1     |     33           |
| sipsa_diario  | fecha                | object              |  383718 |       0 |        0    |     1418 |            |                  |
| sipsa_diario  | fecha_creacion       | datetime64[us, UTC] |  383718 |       0 |        0    |     2657 |            |                  |
| sipsa_diario  | precio_cop_kg        | int64               |  383718 |       0 |        0    |     7328 |    270     |  15500           |
| sipsa_diario  | producto             | str                 |  383718 |       0 |        0    |       33 |            |                  |
| sipsa_diario  | registro_id          | Int64               |  383718 |       0 |        0    |   383718 | 310785     | 694819           |
| sipsa_diario  | es_variedad          | bool                |  383718 |       0 |        0    |        2 |      0     |      1           |
| sipsa_diario  | producto_base        | str                 |  383718 |       0 |        0    |       33 |            |                  |
| sipsa_diario  | anio                 | int32               |  383718 |       0 |        0    |        6 |   2020     |   2026           |
| sipsa_diario  | mes                  | int32               |  383718 |       0 |        0    |       12 |      1     |     12           |
| sipsa_mensual | mercado              | str                 |   33977 |       0 |        0    |       21 |    nan     |    nan           |
| sipsa_mensual | producto             | str                 |   33977 |       0 |        0    |       33 |    nan     |    nan           |
| sipsa_mensual | producto_codigo      | Int64               |   33977 |       0 |        0    |       33 |      1     |     33           |
| sipsa_mensual | anio                 | int32               |   33977 |       0 |        0    |        6 |   2020     |   2026           |
| sipsa_mensual | mes                  | int32               |   33977 |       0 |        0    |       12 |      1     |     12           |
| sipsa_mensual | precio_cop_kg        | float64             |   33977 |       0 |        0    |    27736 |    330.62  |  15225           |
| sipsa_mensual | dias_con_dato        | int64               |   33977 |       0 |        0    |       23 |      1     |     23           |
| sipsa_mensual | precio_min           | int64               |   33977 |       0 |        0    |     3662 |    270     |  14900           |
| sipsa_mensual | precio_max           | int64               |   33977 |       0 |        0    |     4165 |    375     |  15500           |
| sipsa_mensual | item_codigo_fao      | Int64               |   33977 |    2153 |        6.34 |       23 |    116     |    619           |
| sipsa_mensual | item_fao             | str                 |   33977 |    2153 |        6.34 |       23 |    nan     |    nan           |
| sipsa_mensual | tipo_correspondencia | str                 |   33977 |       0 |        0    |        4 |    nan     |    nan           |
| sipsa_mensual | nota                 | str                 |   33977 |   12953 |       38.12 |       14 |    nan     |    nan           |
| clima         | producto             | str                 |    2520 |       0 |        0    |        3 |    nan     |    nan           |
| clima         | departamento         | str                 |    2520 |       0 |        0    |        6 |    nan     |    nan           |
| clima         | lat                  | float64             |    2520 |       0 |        0    |        6 |      2.93  |      6.25        |
| clima         | lon                  | float64             |    2520 |       0 |        0    |        6 |    -75.57  |    -73.36        |
| clima         | elevacion_grilla_m   | float64             |    2520 |       0 |        0    |        6 |   1118.92  |   2557.41        |
| clima         | anio                 | int64               |    2520 |       0 |        0    |       35 |   1991     |   2025           |
| clima         | mes                  | int64               |    2520 |       0 |        0    |       12 |      1     |     12           |
| clima         | PRECTOTCORR          | float64             |    2520 |       0 |        0    |     1010 |      0     |     21.37        |
| clima         | T2M                  | float64             |    2520 |       0 |        0    |      983 |     11.54  |     26.46        |
| clima         | PRECTOTCORR_anomalia | float64             |    2520 |       0 |        0    |     2093 |     -9.733 |     14.604       |
| enso          | trimestre            | str                 |     919 |       0 |        0    |       12 |            |                  |
| enso          | anio                 | int64               |     919 |       0 |        0    |       77 |   1950     |   2026           |
| enso          | mes_central          | int64               |     919 |       0 |        0    |       12 |      1     |     12           |
| enso          | anomalia             | float64             |     919 |       0 |        0    |      307 |     -2.04  |      2.59        |
| enso          | fase                 | str                 |     919 |       0 |        0    |        3 |            |                  |
| enso          | provisional          | bool                |     919 |       0 |        0    |        2 |      0     |      1           |
| insumos       | anio                 | int64               |   56800 |       0 |        0    |       67 |   1960     |   2026           |
| insumos       | mes                  | int64               |   56800 |       0 |        0    |       12 |      1     |     12           |
| insumos       | commodity            | str                 |   56800 |       0 |        0    |       71 |    nan     |    nan           |
| insumos       | unidad               | str                 |   56800 |       0 |        0    |        9 |    nan     |    nan           |
| insumos       | valor_usd            | float64             |   56800 |    6417 |       11.3  |     9941 |      0     |  55385           |

## Homologacion SIPSA - FAOSTAT

Mapeo validado sin problemas contra los datos reales.

| tipo_correspondencia   |   productos |
|:-----------------------|------------:|
| exacta                 |          13 |
| agregada               |          10 |
| generica               |           8 |
| sin_equivalente        |           2 |

Items de FAO que reciben mas de un producto de SIPSA. En estos casos el precio productor de FAO no corresponde a ningun producto de SIPSA por separado:

|   item_codigo_fao | item_fao                        |   productos_sipsa | cuales                                         |
|------------------:|:--------------------------------|------------------:|:-----------------------------------------------|
|               116 | Potatoes                        |                 2 | Papa criolla + Papa negra*                     |
|               463 | Other vegetables, fresh n.e.c.  |                 2 | Habichuela + Remolacha                         |
|               489 | Plantains and cooking bananas   |                 2 | Plátano guineo + Plátano hartón verde          |
|               497 | Lemons and limes                |                 2 | Limón Común + Limón Tahití                     |
|               571 | Mangoes, guavas and mangosteens |                 2 | Guayaba* + Mango tommy                         |
|               603 | Other tropical fruits, n.e.c.   |                 4 | Granadilla + Lulo + Maracuyá + Tomate de árbol |

## Inconsistencias

- Negativos en `faostat_pp.valor`: **0**
- Negativos en `sipsa_diario.precio_cop_kg`: **0**
- Item-anio con exportaciones mayores a produccion mas importaciones: **97** (en toneladas, solo items comparables). De esos, **9** tienen produccion registrada y son inconsistencias a explicar (reexportacion o stock del anio anterior); los otros **88** tienen produccion en cero, o sea que a la fuente le falta publicar ese anio.
- Excluidos por no ser comparables: **295** items de comercio sin produccion primaria (agregados de grupo y productos procesados), equivalentes a 15,863 item-anio.

Las diez inconsistencias reales mas grandes:

| item                        |   anio |   producido |   importado |   exportado |   disponible |
|:----------------------------|-------:|------------:|------------:|------------:|-------------:|
| Coffee, green               |   2021 |    560340   |   102804    |    687866   |     663144   |
| Coffee, green               |   1987 |    651600   |        0    |    661631   |     651600   |
| Coffee, green               |   1999 |    546720   |        0    |    568469   |     546720   |
| Margarine and shortening    |   2022 |     36132.9 |     5198.19 |     48100   |      41331.1 |
| Evaporated & Condensed Milk |   2001 |     15200   |     1652.7  |     26096.7 |      16852.7 |
| Evaporated & Condensed Milk |   2002 |     18750   |     1335.6  |     22434.3 |      20085.6 |
| Sesame seed                 |   1980 |     12900   |        0    |     12922   |      12900   |
| Sesame seed                 |   1982 |      7200   |        0    |      7454   |       7200   |
| Cream, fresh                |   2005 |       900   |       34    |       968   |        934   |
- Series anuales de precios con huecos: **145**, de las cuales **39** tienen un hueco de mas de 3 anios (no se interpolan, se dejan vacias).
