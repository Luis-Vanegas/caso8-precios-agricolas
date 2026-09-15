// Puente entre las zonas climáticas y los productos de SIPSA.
//
// Existe porque los dos lados usan vocabularios distintos: la configuración de
// zonas dice "Papa" y SIPSA dice "Papa negra*". Además es una relación de
// muchos a muchos: una zona sirve a varios productos y un producto puede tener
// varias zonas.

let
    Ruta = CarpetaProyecto & "\data\interim\zonas\zonas_puente.csv",

    Origen = Csv.Document(
        File.Contents(Ruta),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),

    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"producto_sipsa", type text},
            {"producto_zona", type text},
            {"departamento", type text}
        }
    )
in
    Tipos
