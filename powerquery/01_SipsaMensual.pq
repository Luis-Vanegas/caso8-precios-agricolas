// Precios mayoristas mensuales de SIPSA, ya homologados contra ítems de FAOSTAT.
//
// Entrada: data/interim/sipsa/sipsa_mensual.csv  (o el archivo que exportaste
// desde OpenRefine, si preferís usar ese: cambiá el nombre en Origen).
//
// El CSV viene en UTF-8 con BOM. El código de página 65001 es UTF-8; sin él,
// Excel lee "Limón" como "LimÃ³n".

let
    Ruta = CarpetaProyecto & "\data\interim\sipsa\sipsa_mensual.csv",

    Origen = Csv.Document(
        File.Contents(Ruta),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),

    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"mercado", type text},
            {"producto", type text},
            {"producto_codigo", Int64.Type},
            {"anio", Int64.Type},
            {"mes", Int64.Type},
            {"precio_cop_kg", type number},
            {"dias_con_dato", Int64.Type},
            {"precio_min", type number},
            {"precio_max", type number},
            {"item_codigo_fao", Int64.Type},
            {"item_fao", type text},
            {"tipo_correspondencia", type text},
            {"nota", type text}
        }
    ),

    // Clave de tiempo AAAAMM, la misma que usa el modelo en DuckDB.
    ConPeriodo = Table.AddColumn(Tipos, "periodo", each [anio] * 100 + [mes], Int64.Type),

    // Se marca explícitamente qué filas admiten comparar precio mayorista contra
    // precio productor. Solo las exactas: en las agregadas FAOSTAT mezcla varios
    // productos en un ítem y el margen que salga de ahí es inventado.
    ConComparable = Table.AddColumn(
        ConPeriodo,
        "permite_comparar_precio",
        each [tipo_correspondencia] = "exacta",
        type logical
    ),

    // Un mes con dos días de dato no vale lo mismo que uno con veinte.
    ConConfianza = Table.AddColumn(
        ConComparable,
        "confianza_mes",
        each if [dias_con_dato] >= 15 then "alta"
             else if [dias_con_dato] >= 5 then "media"
             else "baja",
        type text
    )
in
    ConConfianza
