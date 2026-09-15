// Precio al productor de FAOSTAT para Colombia, en pesos por tonelada.
//
// Se filtra al elemento 5530 (Producer Price LCU/tonne). Los otros tres
// elementos del dominio son la misma serie en USD, en moneda local estándar y
// como índice: mezclarlos multiplicaría cada serie por cuatro.
//
// La unidad es COP por TONELADA. SIPSA está en COP por KILOGRAMO. Se convierte
// acá para que la comparación sea posible; olvidar esto da un error de mil veces.

let
    Ruta = CarpetaProyecto & "\data\interim\faostat\faostat_pp.csv",

    Origen = Csv.Document(
        File.Contents(Ruta),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),

    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"item_codigo", Int64.Type},
            {"item", type text},
            {"elemento_codigo", Int64.Type},
            {"elemento", type text},
            {"anio", Int64.Type},
            {"mes_codigo", Int64.Type},
            {"unidad", type text},
            {"valor", type number},
            {"flag", type text},
            {"frecuencia", type text}
        }
    ),

    SoloPrecioLocal = Table.SelectRows(
        Tipos, each [elemento_codigo] = 5530 and [valor] <> null
    ),

    // Los códigos de mes de FAOSTAT son 7000 + número de mes. El 7021 es el
    // agregado anual, que NO es un mes y ya viene marcado en `frecuencia`.
    ConMes = Table.AddColumn(
        SoloPrecioLocal,
        "mes",
        each if [frecuencia] = "mensual" then [mes_codigo] - 7000 else null,
        Int64.Type
    ),

    ConPeriodo = Table.AddColumn(
        ConMes,
        "periodo",
        each if [mes] <> null then [anio] * 100 + [mes] else null,
        Int64.Type
    ),

    // De COP por tonelada a COP por kilogramo.
    ConPrecioKg = Table.AddColumn(
        ConPeriodo, "precio_productor_cop_kg", each [valor] / 1000, type number
    ),

    // El flag dice de dónde sale el número. "A" es cifra oficial; el resto es
    // estimado, imputado o de una organización externa, y eso hay que mostrarlo.
    ConOrigen = Table.AddColumn(
        ConPrecioKg,
        "es_cifra_oficial",
        each [flag] = "A",
        type logical
    )
in
    ConOrigen
