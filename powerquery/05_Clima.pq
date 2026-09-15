// Clima mensual por zona productora, desde NASA POWER ya limpio.
//
// Se usa la ANOMALÍA y no el valor absoluto: la grilla de POWER promedia el
// relieve y en Colombia eso deforma las temperaturas absolutas (a Villavicencio,
// a 467 m, le asigna 1.392 m). La anomalía compara cada mes contra el promedio
// histórico del mismo mes en la misma celda, así que el sesgo se cancela.

let
    Ruta = CarpetaProyecto & "\data\interim\clima\clima.csv",

    Origen = Csv.Document(
        File.Contents(Ruta),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),

    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"producto", type text},
            {"departamento", type text},
            {"lat", type number},
            {"lon", type number},
            {"elevacion_grilla_m", type number},
            {"anio", Int64.Type},
            {"mes", Int64.Type},
            {"PRECTOTCORR", type number},
            {"T2M", type number},
            {"PRECTOTCORR_anomalia", type number}
        }
    ),

    Renombrado = Table.RenameColumns(
        Tipos,
        {
            {"PRECTOTCORR", "precipitacion_mm_dia"},
            {"T2M", "temperatura_c"},
            {"PRECTOTCORR_anomalia", "precipitacion_anomalia"}
        }
    )
in
    Renombrado
