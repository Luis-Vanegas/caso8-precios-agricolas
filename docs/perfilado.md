# Perfilado de las tablas limpias

Generado por `scripts/preparar.py`. Una fila por columna de cada tabla.

## Resumen por tabla

| tabla | filas | columnas | duplicados por clave |
|---|---:|---:|---:|
| faostat_pp | 13,489 | 17 | 0 |
| faostat_qcl | 21,346 | 16 | 0 |
| faostat_tcl | 79,395 | 16 | 0 |
| faostat_fbs | 26,916 | 16 | 0 |
| faostat_qv | 20,820 | 15 | 0 |
| faostat_pe | 515 | 16 | 0 |
| sipsa_diario | 398,398 | 11 | 0 |
| sipsa_mensual | 34,964 | 14 | 0 |
| clima | 3,879 | 12 | 0 |
| enso | 921 | 6 | 0 |
| insumos | 56,942 | 5 | 0 |
| zonas_puente | 9 | 3 | 0 |
| sipsa_semanal | 257,704 | 18 | 0 |
| sipsa_abastecimiento | 171,146 | 14 | 0 |
| clima_diario | 20,296 | 8 | 0 |
| clima_estacional | 40 | 9 | 0 |
| ideam_estaciones | 26,110 | 24 | 0 |
| ideam_depto | 1,197 | 7 | 0 |

## Columnas

| tabla                | columna              | tipo                |   filas |   nulos |   pct_nulos |   unicos |       minimo |           maximo |
|:---------------------|:---------------------|:--------------------|--------:|--------:|------------:|---------:|-------------:|-----------------:|
| faostat_pp           | area_codigo          | int64               |   13489 |       0 |        0    |        1 |     44       |     44           |
| faostat_pp           | area_m49             | str                 |   13489 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pp           | area                 | str                 |   13489 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pp           | item_codigo          | int64               |   13489 |       0 |        0    |      106 |     15       |   2051           |
| faostat_pp           | item_cpc             | str                 |   13489 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_pp           | item                 | str                 |   13489 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_pp           | elemento_codigo      | int64               |   13489 |       0 |        0    |        4 |   5530       |   5539           |
| faostat_pp           | elemento             | str                 |   13489 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_pp           | anio_codigo          | int64               |   13489 |       0 |        0    |       35 |   1991       |   2025           |
| faostat_pp           | anio                 | Int64               |   13489 |       0 |        0    |       35 |   1991       |   2025           |
| faostat_pp           | mes_codigo           | int64               |   13489 |       0 |        0    |       13 |   7001       |   7021           |
| faostat_pp           | mes_nombre           | str                 |   13489 |       0 |        0    |       13 |    nan       |    nan           |
| faostat_pp           | unidad               | str                 |   13489 |    3546 |       26.29 |        3 |    nan       |    nan           |
| faostat_pp           | valor                | float64             |   13489 |       0 |        0    |    10236 |      1.6     |      4.23376e+07 |
| faostat_pp           | flag                 | str                 |   13489 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_pp           | dominio              | str                 |   13489 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pp           | frecuencia           | str                 |   13489 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_qcl          | area_codigo          | int64               |   21346 |       0 |        0    |        1 |     44       |     44           |
| faostat_qcl          | area_m49             | str                 |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qcl          | area                 | str                 |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qcl          | item_codigo          | int64               |   21346 |       0 |        0    |      168 |     15       |  17530           |
| faostat_qcl          | item_cpc             | str                 |   21346 |       0 |        0    |      168 |    nan       |    nan           |
| faostat_qcl          | item                 | str                 |   21346 |       0 |        0    |      168 |    nan       |    nan           |
| faostat_qcl          | elemento_codigo      | int64               |   21346 |       0 |        0    |       14 |   5111       |   5513           |
| faostat_qcl          | elemento             | str                 |   21346 |       0 |        0    |        8 |    nan       |    nan           |
| faostat_qcl          | anio_codigo          | int64               |   21346 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qcl          | anio                 | Int64               |   21346 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qcl          | unidad               | str                 |   21346 |       0 |        0    |       10 |    nan       |    nan           |
| faostat_qcl          | valor                | float64             |   21346 |     878 |        4.11 |    13589 |      0       |      4.06869e+07 |
| faostat_qcl          | flag                 | str                 |   21346 |       0 |        0    |        5 |    nan       |    nan           |
| faostat_qcl          | nota                 | object              |   21346 |   20796 |       97.42 |        1 |    nan       |    nan           |
| faostat_qcl          | dominio              | str                 |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qcl          | frecuencia           | str                 |   21346 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl          | area_codigo          | int64               |   79395 |       0 |        0    |        1 |     44       |     44           |
| faostat_tcl          | area_m49             | str                 |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl          | area                 | str                 |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl          | item_codigo          | int64               |   79395 |       0 |        0    |      444 |     10       |   2076           |
| faostat_tcl          | item_cpc             | str                 |   79395 |       0 |        0    |      444 |    nan       |    nan           |
| faostat_tcl          | item                 | str                 |   79395 |       0 |        0    |      444 |    nan       |    nan           |
| faostat_tcl          | elemento_codigo      | int64               |   79395 |       0 |        0    |        8 |   5608       |   5922           |
| faostat_tcl          | elemento             | str                 |   79395 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_tcl          | anio_codigo          | int64               |   79395 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_tcl          | anio                 | Int64               |   79395 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_tcl          | unidad               | str                 |   79395 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_tcl          | valor                | float64             |   79395 |       0 |        0    |    20847 |      0       |      7.74134e+07 |
| faostat_tcl          | flag                 | str                 |   79395 |       0 |        0    |        4 |    nan       |    nan           |
| faostat_tcl          | nota                 | object              |   79395 |   77032 |       97.02 |        1 |    nan       |    nan           |
| faostat_tcl          | dominio              | str                 |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_tcl          | frecuencia           | str                 |   79395 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs          | area_codigo          | int64               |   26916 |       0 |        0    |        1 |     44       |     44           |
| faostat_fbs          | area_m49             | str                 |   26916 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs          | area                 | str                 |   26916 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs          | item_codigo          | int64               |   26916 |       0 |        0    |      123 |   2501       |   2961           |
| faostat_fbs          | item_fbs             | str                 |   26916 |       0 |        0    |      123 |    nan       |    nan           |
| faostat_fbs          | item                 | str                 |   26916 |       0 |        0    |      120 |    nan       |    nan           |
| faostat_fbs          | elemento_codigo      | int64               |   26916 |       0 |        0    |       26 |    501       |   5911           |
| faostat_fbs          | elemento             | str                 |   26916 |       0 |        0    |       26 |    nan       |    nan           |
| faostat_fbs          | anio_codigo          | int64               |   26916 |       0 |        0    |       15 |   2010       |   2024           |
| faostat_fbs          | anio                 | Int64               |   26916 |       0 |        0    |       15 |   2010       |   2024           |
| faostat_fbs          | unidad               | str                 |   26916 |      60 |        0.22 |        8 |    nan       |    nan           |
| faostat_fbs          | valor                | float64             |   26916 |       0 |        0    |     8018 |  -4737       |      5.97574e+07 |
| faostat_fbs          | flag                 | str                 |   26916 |       0 |        0    |        3 |    nan       |    nan           |
| faostat_fbs          | nota                 | float64             |   26916 |   26916 |      100    |        0 |    nan       |    nan           |
| faostat_fbs          | dominio              | str                 |   26916 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_fbs          | frecuencia           | str                 |   26916 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv           | area_codigo          | int64               |   20820 |       0 |        0    |        1 |     44       |     44           |
| faostat_qv           | area_m49             | str                 |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv           | area                 | str                 |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv           | item_codigo          | int64               |   20820 |       0 |        0    |      106 |     15       |   2057           |
| faostat_qv           | item_cpc             | str                 |   20820 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_qv           | item                 | str                 |   20820 |       0 |        0    |      106 |    nan       |    nan           |
| faostat_qv           | elemento_codigo      | int64               |   20820 |       0 |        0    |        5 |     55       |    152           |
| faostat_qv           | elemento             | str                 |   20820 |       0 |        0    |        5 |    nan       |    nan           |
| faostat_qv           | anio_codigo          | int64               |   20820 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qv           | anio                 | Int64               |   20820 |       0 |        0    |       64 |   1961       |   2024           |
| faostat_qv           | unidad               | str                 |   20820 |       0 |        0    |        3 |    nan       |    nan           |
| faostat_qv           | valor                | float64             |   20820 |       0 |        0    |    18860 |      3       |      2.14323e+11 |
| faostat_qv           | flag                 | str                 |   20820 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_qv           | dominio              | str                 |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_qv           | frecuencia           | str                 |   20820 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe           | area_codigo          | int64               |     515 |       0 |        0    |        1 |     44       |     44           |
| faostat_pe           | area_m49             | str                 |     515 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe           | area                 | str                 |     515 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe           | elemento_codigo      | str                 |     515 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_pe           | elemento             | str                 |     515 |       0 |        0    |        2 |    nan       |    nan           |
| faostat_pe           | moneda_iso           | str                 |     515 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe           | moneda               | str                 |     515 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe           | anio_codigo          | int64               |     515 |       0 |        0    |       57 |   1970       |   2026           |
| faostat_pe           | anio                 | Int64               |     515 |       0 |        0    |       57 |   1970       |   2026           |
| faostat_pe           | mes_codigo           | int64               |     515 |       0 |        0    |       13 |   7001       |   7021           |
| faostat_pe           | mes_nombre           | str                 |     515 |       0 |        0    |       13 |    nan       |    nan           |
| faostat_pe           | unidad               | float64             |     515 |     515 |      100    |        0 |    nan       |    nan           |
| faostat_pe           | valor                | float64             |     515 |       0 |        0    |      456 |     17.9     |   4922.3         |
| faostat_pe           | flag                 | str                 |     515 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe           | dominio              | str                 |     515 |       0 |        0    |        1 |    nan       |    nan           |
| faostat_pe           | frecuencia           | str                 |     515 |       0 |        0    |        2 |    nan       |    nan           |
| sipsa_diario         | mercado              | str                 |  398398 |       0 |        0    |       20 |              |                  |
| sipsa_diario         | producto_codigo      | Int64               |  398398 |       0 |        0    |       33 |      1       |     33           |
| sipsa_diario         | fecha                | object              |  398398 |       0 |        0    |     1471 |              |                  |
| sipsa_diario         | fecha_creacion       | datetime64[us, UTC] |  398398 |       0 |        0    |     2760 |              |                  |
| sipsa_diario         | precio_cop_kg        | int64               |  398398 |       0 |        0    |     7373 |    270       |  15500           |
| sipsa_diario         | producto             | str                 |  398398 |       0 |        0    |       33 |              |                  |
| sipsa_diario         | registro_id          | Int64               |  398398 |       0 |        0    |   398398 | 310785       | 709499           |
| sipsa_diario         | es_variedad          | bool                |  398398 |       0 |        0    |        2 |      0       |      1           |
| sipsa_diario         | producto_base        | str                 |  398398 |       0 |        0    |       33 |              |                  |
| sipsa_diario         | anio                 | int32               |  398398 |       0 |        0    |        6 |   2020       |   2026           |
| sipsa_diario         | mes                  | int32               |  398398 |       0 |        0    |       12 |      1       |     12           |
| sipsa_mensual        | mercado              | str                 |   34964 |       0 |        0    |       20 |              |                  |
| sipsa_mensual        | producto             | str                 |   34964 |       0 |        0    |       33 |              |                  |
| sipsa_mensual        | producto_codigo      | Int64               |   34964 |       0 |        0    |       33 |      1       |     33           |
| sipsa_mensual        | anio                 | int32               |   34964 |       0 |        0    |        6 |   2020       |   2026           |
| sipsa_mensual        | mes                  | int32               |   34964 |       0 |        0    |       12 |      1       |     12           |
| sipsa_mensual        | precio_cop_kg        | float64             |   34964 |       0 |        0    |    28548 |    330.62    |  15225           |
| sipsa_mensual        | dias_con_dato        | int64               |   34964 |       0 |        0    |       23 |      1       |     23           |
| sipsa_mensual        | precio_min           | int64               |   34964 |       0 |        0    |     3691 |    270       |  14900           |
| sipsa_mensual        | precio_max           | int64               |   34964 |       0 |        0    |     4211 |    375       |  15500           |
| sipsa_mensual        | mes_cerrado          | bool                |   34964 |       0 |        0    |        2 |      0       |      1           |
| sipsa_mensual        | item_codigo_fao      | Int64               |   34964 |    2217 |        6.34 |       23 |    116       |    619           |
| sipsa_mensual        | item_fao             | str                 |   34964 |    2217 |        6.34 |       23 |              |                  |
| sipsa_mensual        | tipo_correspondencia | str                 |   34964 |       0 |        0    |        4 |              |                  |
| sipsa_mensual        | nota                 | str                 |   34964 |   13325 |       38.11 |       14 |              |                  |
| clima                | producto             | str                 |    3879 |       0 |        0    |        6 |    nan       |    nan           |
| clima                | departamento         | str                 |    3879 |       0 |        0    |        8 |    nan       |    nan           |
| clima                | lat                  | float64             |    3879 |       0 |        0    |        8 |      2.93    |      7.89        |
| clima                | lon                  | float64             |    3879 |       0 |        0    |        8 |    -75.68    |    -72.5         |
| clima                | elevacion_grilla_m   | float64             |    3879 |       0 |        0    |        8 |    741.14    |   2557.41        |
| clima                | anio                 | int64               |    3879 |       0 |        0    |       36 |   1991       |   2026           |
| clima                | mes                  | int64               |    3879 |       0 |        0    |       12 |      1       |     12           |
| clima                | PRECTOTCORR          | float64             |    3879 |       0 |        0    |     1090 |      0       |     21.42        |
| clima                | T2M                  | float64             |    3879 |       0 |        0    |     1335 |     11.54    |     29.24        |
| clima                | fuente               | str                 |    3879 |       0 |        0    |        2 |    nan       |    nan           |
| clima                | dias_con_dato        | float64             |    3879 |    3870 |       99.77 |        1 |     23       |     23           |
| clima                | PRECTOTCORR_anomalia | float64             |    3879 |       0 |        0    |     2663 |     -9.933   |     14.555       |
| enso                 | trimestre            | str                 |     921 |       0 |        0    |       12 |              |                  |
| enso                 | anio                 | int64               |     921 |       0 |        0    |       77 |   1950       |   2026           |
| enso                 | mes_central          | int64               |     921 |       0 |        0    |       12 |      1       |     12           |
| enso                 | anomalia             | float64             |     921 |       0 |        0    |      309 |     -2.04    |      2.59        |
| enso                 | fase                 | str                 |     921 |       0 |        0    |        3 |              |                  |
| enso                 | provisional          | bool                |     921 |       0 |        0    |        2 |      0       |      1           |
| insumos              | anio                 | int64               |   56942 |       0 |        0    |       67 |   1960       |   2026           |
| insumos              | mes                  | int64               |   56942 |       0 |        0    |       12 |      1       |     12           |
| insumos              | commodity            | str                 |   56942 |       0 |        0    |       71 |    nan       |    nan           |
| insumos              | unidad               | str                 |   56942 |       0 |        0    |        9 |    nan       |    nan           |
| insumos              | valor_usd            | float64             |   56942 |    6424 |       11.28 |     9930 |      0       |  55385           |
| zonas_puente         | producto_sipsa       | str                 |       9 |       0 |        0    |        7 |              |                  |
| zonas_puente         | producto_zona        | str                 |       9 |       0 |        0    |        4 |              |                  |
| zonas_puente         | departamento         | str                 |       9 |       0 |        0    |        4 |              |                  |
| sipsa_semanal        | art_id               | int64               |  257704 |       0 |        0    |      351 |      1       |   6764           |
| sipsa_semanal        | articulo             | str                 |  257704 |       0 |        0    |      351 |              |                  |
| sipsa_semanal        | fuen_id              | int64               |  257704 |       0 |        0    |       80 |      1       |   7209           |
| sipsa_semanal        | semana_inicio        | datetime64[us]      |  257704 |       0 |        0    |       57 |              |                  |
| sipsa_semanal        | precio               | int64               |  257704 |       0 |        0    |    20967 |    250       | 273333           |
| sipsa_semanal        | precio_min           | int64               |  257704 |       0 |        0    |     7258 |    182       | 270000           |
| sipsa_semanal        | precio_max           | int64               |  257704 |       0 |        0    |     7295 |    264       | 280000           |
| sipsa_semanal        | unidad               | str                 |  257704 |       0 |        0    |        3 |              |                  |
| sipsa_semanal        | anio                 | int32               |  257704 |       0 |        0    |        2 |   2025       |   2026           |
| sipsa_semanal        | mes                  | int32               |  257704 |       0 |        0    |       12 |      1       |     12           |
| sipsa_semanal        | periodo              | int32               |  257704 |       0 |        0    |       14 | 202510       | 202611           |
| sipsa_semanal        | mercado              | str                 |  257704 |       0 |        0    |       80 |              |                  |
| sipsa_semanal        | ciudad               | str                 |  257704 |       0 |        0    |       59 |              |                  |
| sipsa_semanal        | departamento         | str                 |  257704 |       0 |        0    |       24 |              |                  |
| sipsa_semanal        | dpto_codigo          | str                 |  257704 |       0 |        0    |       24 |              |                  |
| sipsa_semanal        | producto             | str                 |  257704 |       0 |        0    |      136 |              |                  |
| sipsa_semanal        | grupo_dane           | str                 |  257704 |       0 |        0    |        8 |              |                  |
| sipsa_semanal        | en_canasta           | bool                |  257704 |       0 |        0    |        2 |      0       |      1           |
| sipsa_abastecimiento | art_id               | int64               |  171146 |       0 |        0    |      194 |      1       |   6746           |
| sipsa_abastecimiento | articulo             | str                 |  171146 |       0 |        0    |      194 |              |                  |
| sipsa_abastecimiento | fuen_id              | int64               |  171146 |       0 |        0    |       32 |      1       |   4389           |
| sipsa_abastecimiento | anio                 | int32               |  171146 |       0 |        0    |        6 |   2020       |   2026           |
| sipsa_abastecimiento | mes                  | int32               |  171146 |       0 |        0    |       12 |      1       |     12           |
| sipsa_abastecimiento | toneladas            | int64               |  171146 |       0 |        0    |     3791 |      0       |  29690           |
| sipsa_abastecimiento | periodo              | int32               |  171146 |       0 |        0    |       59 | 202002       | 202610           |
| sipsa_abastecimiento | mercado              | str                 |  171146 |       0 |        0    |       32 |              |                  |
| sipsa_abastecimiento | ciudad               | str                 |  171146 |       0 |        0    |       23 |              |                  |
| sipsa_abastecimiento | departamento         | str                 |  171146 |       0 |        0    |       21 |              |                  |
| sipsa_abastecimiento | dpto_codigo          | str                 |  171146 |       0 |        0    |       21 |              |                  |
| sipsa_abastecimiento | producto             | str                 |  171146 |       0 |        0    |      134 |              |                  |
| sipsa_abastecimiento | grupo_dane           | str                 |  171146 |       0 |        0    |        8 |              |                  |
| sipsa_abastecimiento | en_canasta           | bool                |  171146 |       0 |        0    |        2 |      0       |      1           |
| clima_diario         | departamento         | str                 |   20296 |       0 |        0    |        8 |    nan       |    nan           |
| clima_diario         | fecha                | datetime64[us]      |   20296 |       0 |        0    |     2537 |    nan       |    nan           |
| clima_diario         | precipitacion_mm     | float64             |   20296 |       0 |        0    |      610 |      0       |    188.3         |
| clima_diario         | temp_max             | float64             |   20296 |       0 |        0    |      279 |     12.3     |     40.7         |
| clima_diario         | temp_min             | float64             |   20296 |       0 |        0    |      250 |      1.1     |     28.8         |
| clima_diario         | tipo                 | str                 |   20296 |       0 |        0    |        2 |    nan       |    nan           |
| clima_diario         | dpto_codigo          | str                 |   20296 |       0 |        0    |        8 |    nan       |    nan           |
| clima_diario         | fuente               | str                 |   20296 |       0 |        0    |        1 |    nan       |    nan           |
| clima_estacional     | departamento         | str                 |      40 |       0 |        0    |        8 |    nan       |    nan           |
| clima_estacional     | dpto_codigo          | str                 |      40 |       0 |        0    |        8 |    nan       |    nan           |
| clima_estacional     | anio                 | int64               |      40 |       0 |        0    |        2 |   2026       |   2027           |
| clima_estacional     | mes                  | int64               |      40 |       0 |        0    |        5 |      1       |     12           |
| clima_estacional     | periodo              | int64               |      40 |       0 |        0    |        5 | 202612       | 202704           |
| clima_estacional     | precip_p10           | float64             |      40 |       0 |        0    |       40 |      2.4     |    430.2         |
| clima_estacional     | precip_p50           | float64             |      40 |       0 |        0    |       39 |     12       |    556.3         |
| clima_estacional     | precip_p90           | float64             |      40 |       0 |        0    |       40 |     36.4     |    706.1         |
| clima_estacional     | anomalia_p50         | float64             |      40 |       0 |        0    |       40 |   -400       |    235.1         |
| ideam_estaciones     | codigoestacion       | str                 |   26110 |       0 |        0    |      467 |              |                  |
| ideam_estaciones     | codigosensor         | str                 |   26110 |       0 |        0    |        4 |              |                  |
| ideam_estaciones     | fechaobservacion     | str                 |   26110 |   26108 |       99.99 |        1 |              |                  |
| ideam_estaciones     | valorobservado       | str                 |   26110 |   26108 |       99.99 |        1 |              |                  |
| ideam_estaciones     | nombreestacion       | str                 |   26110 |       0 |        0    |      941 |              |                  |
| ideam_estaciones     | departamento         | str                 |   26110 |       0 |        0    |        8 |              |                  |
| ideam_estaciones     | municipio            | str                 |   26110 |       0 |        0    |      494 |              |                  |
| ideam_estaciones     | zonahidrografica     | str                 |   26110 |   26108 |       99.99 |        1 |              |                  |
| ideam_estaciones     | latitud              | float64             |   26110 |       0 |        0    |      765 |      1.67583 |      8.63833     |
| ideam_estaciones     | longitud             | float64             |   26110 |       0 |        0    |      692 |    -76.7619  |    -71.3357      |
| ideam_estaciones     | descripcionsensor    | str                 |   26110 |   26108 |       99.99 |        2 |              |                  |
| ideam_estaciones     | unidadmedida         | str                 |   26110 |   26108 |       99.99 |        1 |              |                  |
| ideam_estaciones     | variable             | str                 |   26110 |       0 |        0    |        3 |              |                  |
| ideam_estaciones     | suma                 | float64             |   26110 |       2 |        0.01 |    14684 |      0       |      1.12201e+06 |
| ideam_estaciones     | promedio             | float64             |   26110 |       2 |        0.01 |    23871 |      0       |     43.1629      |
| ideam_estaciones     | minimo               | float64             |   26110 |       2 |        0.01 |     2380 |      0       |     34.7         |
| ideam_estaciones     | maximo               | float64             |   26110 |       2 |        0.01 |     3056 |      0       |     50           |
| ideam_estaciones     | n_lecturas           | Int64               |   26110 |       2 |        0.01 |     5332 |      1       |  77518           |
| ideam_estaciones     | anio                 | float64             |   26110 |       2 |        0.01 |        7 |   2020       |   2026           |
| ideam_estaciones     | mes                  | float64             |   26110 |       2 |        0.01 |       12 |      1       |     12           |
| ideam_estaciones     | completitud          | Float64             |   26110 |       2 |        0.01 |     1001 |      0       |      1           |
| ideam_estaciones     | fuera_de_rango       | bool                |   26110 |       0 |        0    |        2 |      0       |      1           |
| ideam_estaciones     | valido               | boolean             |   26110 |       2 |        0.01 |        2 |      0       |      1           |
| ideam_estaciones     | valor                | float64             |   26110 |       2 |        0.01 |    14901 |      0       |  30726.5         |
| ideam_depto          | variable             | str                 |    1197 |       0 |        0    |        2 |    nan       |    nan           |
| ideam_depto          | departamento         | str                 |    1197 |       0 |        0    |        8 |    nan       |    nan           |
| ideam_depto          | anio                 | float64             |    1197 |       0 |        0    |        7 |   2020       |   2026           |
| ideam_depto          | mes                  | float64             |    1197 |       0 |        0    |       12 |      1       |     12           |
| ideam_depto          | valor                | float64             |    1197 |       0 |        0    |     1159 |      0       |    641.5         |
| ideam_depto          | n_estaciones         | int64               |    1197 |       0 |        0    |       61 |      1       |     64           |
| ideam_depto          | anomalia             | float64             |    1197 |       0 |        0    |     1172 |   -313.925   |    348.568       |

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
