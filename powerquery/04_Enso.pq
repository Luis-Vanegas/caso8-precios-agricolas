// Fase El Niño / La Niña por mes, desde el archivo del NOAA ya limpio.
//
// El ONI es trimestral (media móvil de tres meses). `mes_central` es el mes al
// que corresponde cada trimestre: DJF centra en enero, JJA en julio.

let
    Ruta = CarpetaProyecto & "\data\interim\enso\enso.csv",

    Origen = Csv.Document(
        File.Contents(Ruta),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),

    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"trimestre", type text},
            {"anio", Int64.Type},
            {"mes_central", Int64.Type},
            {"anomalia", type number},
            {"fase", type text},
            {"provisional", type logical}
        }
    ),

    Renombrado = Table.RenameColumns(Tipos, {{"mes_central", "mes"}})
in
    Renombrado
