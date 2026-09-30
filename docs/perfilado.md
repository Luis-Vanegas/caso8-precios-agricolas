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
| sipsa_diario | 387,063 | 11 | 0 |
| sipsa_mensual | 33,953 | 14 | 0 |
| clima | 3,861 | 12 | 0 |
| enso | 919 | 6 | 0 |
| insumos | 56,800 | 5 | 0 |
| zonas_puente | 9 | 3 | 0 |
| ideam_estaciones | 14,905 | 19 | 0 |
| ideam_depto | 600 | 7 | 0 |

## Columnas

| tabla            | columna              | tipo                |   filas |   nulos |   pct_nulos |   unicos |       minimo |           maximo |
|:-----------------|:---------------------|:--------------------|--------:|--------:|------------:|---------:|-------------:|-----------------:|
| faostat_pp       | area_codigo          | int64               |   13489 |       0 |        0    |        1 |     44       |     44           |
| faostat_pp       | area_m49             | object              |   13489 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pp       | area                 | object              |   13489 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pp       | item_codigo          | int64               |   13489 |       0 |        0    |      106 |     15       |   2051           |
| faostat_pp       | item_cpc             | object              |   13489 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_pp       | item                 | object              |   13489 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_pp       | elemento_codigo      | int64               |   13489 |       0 |        0    |        4 |   5530       |   5539           |
| faostat_pp       | elemento             | object              |   13489 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_pp       | anio_codigo          | int64               |   13489 |       0 |        0    |       35 |   1991       |   2025           |
| faostat_pp       | anio                 | Int64               |   13489 |       0 |        0    |       35 |   1991       |   2025           |
| faostat_pp       | mes_codigo           | int64               |   13489 |       0 |        0    |       13 |   7001       |   7021           |
| faostat_pp       | mes_nombre           | object              |   13489 |       0 |        0    |       13 |    nan       |    nan           |
| faostat_pp       | unidad               | object              |   13489 |    3546 |       26.29 |        3 |    nan       |    nan           |
| faostat_pp       | valor                | float64             |   13489 |       0 |        0    |    10236 |      1.6     |      4.23376e+07 |
| faostat_pp       | flag                 | object              |   13489 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_pp       | dominio              | object              |   13489 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pp       | frecuencia           | object              |   13489 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_qcl      | area_codigo          | int64               |   21346 |       0 |        0    |        1 |     44       |     44           |
| faostat_qcl      | area_m49             | object              |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qcl      | area                 | object              |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qcl      | item_codigo          | int64               |   21346 |       0 |        0    |      168 |     15       |  17530           |
| faostat_qcl      | item_cpc             | object              |   21346 |       0 |        0    |      168 |    nan       |    nan           |
| faostat_qcl      | item                 | object              |   21346 |       0 |        0    |      168 |    nan       |    nan           |
| faostat_qcl      | elemento_codigo      | int64               |   21346 |       0 |        0    |       14 |   5111       |   5513           |
| faostat_qcl      | elemento             | object              |   21346 |       0 |        0    |        8 |    nan       |    nan           |
| faostat_qcl      | anio_codigo          | int64               |   21346 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qcl      | anio                 | Int64               |   21346 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qcl      | unidad               | object              |   21346 |       0 |        0    |       10 |    nan       |    nan           |
| faostat_qcl      | valor                | float64             |   21346 |     878 |        4.11 |    13589 |      0       |      4.06869e+07 |
| faostat_qcl      | flag                 | object              |   21346 |       0 |        0    |        5 |    nan       |    nan           |
| faostat_qcl      | nota                 | object              |   21346 |   20796 |       97.42 |        1 |    nan       |    nan           |
| faostat_qcl      | dominio              | object              |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qcl      | frecuencia           | object              |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl      | area_codigo          | int64               |   79395 |       0 |        0    |        1 |     44       |     44           |
| faostat_tcl      | area_m49             | object              |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl      | area                 | object              |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl      | item_codigo          | int64               |   79395 |       0 |        0    |      444 |     10       |   2076           |
| faostat_tcl      | item_cpc             | object              |   79395 |       0 |        0    |      444 |    nan       |    nan           |
| faostat_tcl      | item                 | object              |   79395 |       0 |        0    |      444 |    nan       |    nan           |
| faostat_tcl      | elemento_codigo      | int64               |   79395 |       0 |        0    |        8 |   5608       |   5922           |
| faostat_tcl      | elemento             | object              |   79395 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_tcl      | anio_codigo          | int64               |   79395 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_tcl      | anio                 | Int64               |   79395 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_tcl      | unidad               | object              |   79395 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_tcl      | valor                | float64             |   79395 |       0 |        0    |    20847 |      0       |      7.74134e+07 |
| faostat_tcl      | flag                 | object              |   79395 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_tcl      | nota                 | object              |   79395 |   77032 |       97.02 |        1 |    nan       |    nan           |
| faostat_tcl      | dominio              | object              |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl      | frecuencia           | object              |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs      | area_codigo          | int64               |   24399 |       0 |        0    |        1 |     44       |     44           |
| faostat_fbs      | area_m49             | object              |   24399 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs      | area                 | object              |   24399 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs      | item_codigo          | int64               |   24399 |       0 |        0    |      122 |   2501       |   2961           |
| faostat_fbs      | item_fbs             | object              |   24399 |       0 |        0    |      122 |    nan       |    nan           |
| faostat_fbs      | item                 | object              |   24399 |       0 |        0    |      119 |    nan       |    nan           |
| faostat_fbs      | elemento_codigo      | int64               |   24399 |       0 |        0    |       20 |    511       |   5911           |
| faostat_fbs      | elemento             | object              |   24399 |       0 |        0    |       20 |    nan       |    nan           |
| faostat_fbs      | anio_codigo          | int64               |   24399 |       0 |        0    |       14 |   2010       |   2023           |
| faostat_fbs      | anio                 | Int64               |   24399 |       0 |        0    |       14 |   2010       |   2023           |
| faostat_fbs      | unidad               | object              |   24399 |       0 |        0    |        7 |    nan       |    nan           |
| faostat_fbs      | valor                | float64             |   24399 |       0 |        0    |     7471 |  -4737       |      5.97041e+07 |
| faostat_fbs      | flag                 | object              |   24399 |       0 |        0    |        3 |    nan       |    nan           |
| faostat_fbs      | nota                 | float64             |   24399 |   24399 |      100    |        0 |    nan       |    nan           |
| faostat_fbs      | dominio              | object              |   24399 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs      | frecuencia           | object              |   24399 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv       | area_codigo          | int64               |   20820 |       0 |        0    |        1 |     44       |     44           |
| faostat_qv       | area_m49             | object              |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv       | area                 | object              |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv       | item_codigo          | int64               |   20820 |       0 |        0    |      106 |     15       |   2057           |
| faostat_qv       | item_cpc             | object              |   20820 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_qv       | item                 | object              |   20820 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_qv       | elemento_codigo      | int64               |   20820 |       0 |        0    |        5 |     55       |    152           |
| faostat_qv       | elemento             | object              |   20820 |       0 |        0    |        5 |    nan       |    nan           |
| faostat_qv       | anio_codigo          | int64               |   20820 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qv       | anio                 | Int64               |   20820 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qv       | unidad               | object              |   20820 |       0 |        0    |        3 |    nan       |    nan           |
| faostat_qv       | valor                | float64             |   20820 |       0 |        0    |    18860 |      3       |      2.14323e+11 |
| faostat_qv       | flag                 | object              |   20820 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_qv       | dominio              | object              |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv       | frecuencia           | object              |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe       | area_codigo          | int64               |     511 |       0 |        0    |        1 |     44       |     44           |
| faostat_pe       | area_m49             | object              |     511 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe       | area                 | object              |     511 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe       | elemento_codigo      | object              |     511 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_pe       | elemento             | object              |     511 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_pe       | moneda_iso           | object              |     511 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe       | moneda               | object              |     511 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe       | anio_codigo          | int64               |     511 |       0 |        0    |       57 |   1970       |   2026           |
| faostat_pe       | anio                 | Int64               |     511 |       0 |        0    |       57 |   1970       |   2026           |
| faostat_pe       | mes_codigo           | int64               |     511 |       0 |        0    |       13 |   7001       |   7021           |
| faostat_pe       | mes_nombre           | object              |     511 |       0 |        0    |       13 |    nan       |    nan           |
| faostat_pe       | unidad               | float64             |     511 |     511 |      100    |        0 |    nan       |    nan           |
| faostat_pe       | valor                | float64             |     511 |       0 |        0    |      453 |     17.9     |   4922.3         |
| faostat_pe       | flag                 | object              |     511 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe       | dominio              | object              |     511 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe       | frecuencia           | object              |     511 |       0 |        0    |        2 |    nan       |    nan           |
| sipsa_diario     | mercado              | object              |  387063 |       0 |        0    |       20 |              |                  |
| sipsa_diario     | producto_codigo      | Int64               |  387063 |       0 |        0    |       33 |      1       |     33           |
| sipsa_diario     | fecha                | object              |  387063 |       0 |        0    |     1430 |              |                  |
| sipsa_diario     | fecha_creacion       | datetime64[ns, UTC] |  387063 |       0 |        0    |     2681 |              |                  |
| sipsa_diario     | precio_cop_kg        | int64               |  387063 |       0 |        0    |     7341 |    270       |  15500           |
| sipsa_diario     | producto             | object              |  387063 |       0 |        0    |       33 |              |                  |
| sipsa_diario     | registro_id          | Int64               |  387063 |       0 |        0    |   387063 | 310785       | 698164           |
| sipsa_diario     | es_variedad          | bool                |  387063 |       0 |        0    |        2 |      0       |      1           |
| sipsa_diario     | producto_base        | object              |  387063 |       0 |        0    |       33 |              |                  |
| sipsa_diario     | anio                 | int32               |  387063 |       0 |        0    |        6 |   2020       |   2026           |
| sipsa_diario     | mes                  | int32               |  387063 |       0 |        0    |       12 |      1       |     12           |
| sipsa_mensual    | mercado              | object              |   33953 |       0 |        0    |       20 |              |                  |
| sipsa_mensual    | producto             | object              |   33953 |       0 |        0    |       33 |              |                  |
| sipsa_mensual    | producto_codigo      | Int64               |   33953 |       0 |        0    |       33 |      1       |     33           |
| sipsa_mensual    | anio                 | int32               |   33953 |       0 |        0    |        6 |   2020       |   2026           |
| sipsa_mensual    | mes                  | int32               |   33953 |       0 |        0    |       12 |      1       |     12           |
| sipsa_mensual    | precio_cop_kg        | float64             |   33953 |       0 |        0    |    27807 |    330.62    |  15225           |
| sipsa_mensual    | dias_con_dato        | int64               |   33953 |       0 |        0    |       23 |      1       |     23           |
| sipsa_mensual    | precio_min           | int64               |   33953 |       0 |        0    |     3655 |    270       |  14900           |
| sipsa_mensual    | precio_max           | int64               |   33953 |       0 |        0    |     4173 |    375       |  15500           |
| sipsa_mensual    | mes_cerrado          | bool                |   33953 |       0 |        0    |        2 |      0       |      1           |
| sipsa_mensual    | item_codigo_fao      | Int64               |   33953 |    2151 |        6.34 |       23 |    116       |    619           |
| sipsa_mensual    | item_fao             | object              |   33953 |    2151 |        6.34 |       23 |              |                  |
| sipsa_mensual    | tipo_correspondencia | object              |   33953 |       0 |        0    |        4 |              |                  |
| sipsa_mensual    | nota                 | object              |   33953 |   12943 |       38.12 |       14 |              |                  |
| clima            | producto             | object              |    3861 |       0 |        0    |        6 |    nan       |    nan           |
| clima            | departamento         | object              |    3861 |       0 |        0    |        8 |    nan       |    nan           |
| clima            | lat                  | float64             |    3861 |       0 |        0    |        8 |      2.93    |      7.89        |
| clima            | lon                  | float64             |    3861 |       0 |        0    |        8 |    -75.68    |    -72.5         |
| clima            | elevacion_grilla_m   | float64             |    3861 |       0 |        0    |        8 |    741.14    |   2557.41        |
| clima            | anio                 | int64               |    3861 |       0 |        0    |       36 |   1991       |   2026           |
| clima            | mes                  | int64               |    3861 |       0 |        0    |       12 |      1       |     12           |
| clima            | PRECTOTCORR          | float64             |    3861 |       0 |        0    |     1089 |      0       |     21.37        |
| clima            | T2M                  | float64             |    3861 |       0 |        0    |     1332 |     11.54    |     29.24        |
| clima            | fuente               | object              |    3861 |       0 |        0    |        2 |    nan       |    nan           |
| clima            | dias_con_dato        | float64             |    3861 |    3852 |       99.77 |        1 |     26       |     26           |
| clima            | PRECTOTCORR_anomalia | float64             |    3861 |       0 |        0    |     2668 |     -9.933   |     14.555       |
| enso             | trimestre            | object              |     919 |       0 |        0    |       12 |              |                  |
| enso             | anio                 | int64               |     919 |       0 |        0    |       77 |   1950       |   2026           |
| enso             | mes_central          | int64               |     919 |       0 |        0    |       12 |      1       |     12           |
| enso             | anomalia             | float64             |     919 |       0 |        0    |      307 |     -2.04    |      2.59        |
| enso             | fase                 | object              |     919 |       0 |        0    |        3 |              |                  |
| enso             | provisional          | bool                |     919 |       0 |        0    |        2 |      0       |      1           |
| insumos          | anio                 | int64               |   56800 |       0 |        0    |       67 |   1960       |   2026           |
| insumos          | mes                  | int64               |   56800 |       0 |        0    |       12 |      1       |     12           |
| insumos          | commodity            | object              |   56800 |       0 |        0    |       71 |    nan       |    nan           |
| insumos          | unidad               | object              |   56800 |       0 |        0    |        9 |    nan       |    nan           |
| insumos          | valor_usd            | float64             |   56800 |    6417 |       11.3  |     9941 |      0       |  55385           |
| zonas_puente     | producto_sipsa       | object              |       9 |       0 |        0    |        7 |              |                  |
| zonas_puente     | producto_zona        | object              |       9 |       0 |        0    |        4 |              |                  |
| zonas_puente     | departamento         | object              |       9 |       0 |        0    |        4 |              |                  |
| ideam_estaciones | codigoestacion       | object              |   14905 |       0 |        0    |      441 |              |                  |
| ideam_estaciones | codigosensor         | object              |   14905 |       0 |        0    |        2 |              |                  |
| ideam_estaciones | nombreestacion       | object              |   14905 |       0 |        0    |      865 |              |                  |
| ideam_estaciones | departamento         | object              |   14905 |       0 |        0    |        8 |              |                  |
| ideam_estaciones | municipio            | object              |   14905 |       0 |        0    |      464 |              |                  |
| ideam_estaciones | latitud              | float64             |   14905 |       0 |        0    |      692 |      1.67583 |      8.63833     |
| ideam_estaciones | longitud             | float64             |   14905 |       0 |        0    |      641 |    -76.7619  |    -71.3357      |
| ideam_estaciones | suma                 | float64             |   14905 |       0 |        0    |     4282 |      0       |  30726.5         |
| ideam_estaciones | promedio             | float64             |   14905 |       0 |        0    |    12769 |      0       |     24.6035      |
| ideam_estaciones | minimo               | float64             |   14905 |       0 |        0    |       12 |      0       |     20.53        |
| ideam_estaciones | maximo               | float64             |   14905 |       0 |        0    |      754 |      0       |     30           |
| ideam_estaciones | n_lecturas           | Int64               |   14905 |       0 |        0    |     4375 |      1       |  77518           |
| ideam_estaciones | variable             | object              |   14905 |       0 |        0    |        1 |              |                  |
| ideam_estaciones | anio                 | int32               |   14905 |       0 |        0    |        7 |   2020       |   2026           |
| ideam_estaciones | mes                  | int32               |   14905 |       0 |        0    |       12 |      1       |     12           |
| ideam_estaciones | completitud          | Float64             |   14905 |       0 |        0    |      986 |      0       |      1           |
| ideam_estaciones | fuera_de_rango       | bool                |   14905 |       0 |        0    |        1 |      0       |      0           |
| ideam_estaciones | valido               | boolean             |   14905 |       0 |        0    |        2 |      0       |      1           |
| ideam_estaciones | valor                | float64             |   14905 |       0 |        0    |     4282 |      0       |  30726.5         |
| ideam_depto      | variable             | object              |     600 |       0 |        0    |        1 |    nan       |    nan           |
| ideam_depto      | departamento         | object              |     600 |       0 |        0    |        8 |    nan       |    nan           |
| ideam_depto      | anio                 | int32               |     600 |       0 |        0    |        7 |   2020       |   2026           |
| ideam_depto      | mes                  | int32               |     600 |       0 |        0    |       12 |      1       |     12           |
| ideam_depto      | valor                | float64             |     600 |       0 |        0    |      570 |      0       |    641.5         |
| ideam_depto      | n_estaciones         | int64               |     600 |       0 |        0    |       60 |      1       |     64           |
| ideam_depto      | anomalia             | float64             |     600 |       0 |        0    |      600 |   -313.925   |    348.042       |

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
