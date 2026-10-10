// Abastecimiento de SIPSA: toneladas que entraron a cada central por mes.
//
// Entrada: data/interim/sipsa/sipsa_abastecimiento.csv (164.274 filas)
//
// El CSV viene en UTF-8 con BOM. El código de página 65001 es UTF-8; sin él,
// Excel lee "Limón" como "LimÃ³n" y "Bogotá" como "BogotÃ¡".
//
// Importante sobre dpto_codigo: es el código DANE de dos dígitos y se deja como
// TEXTO a propósito. Si Excel lo lee como número, Antioquia pasa de "05" a "5"
// y deja de cruzar con el GeoJSON del mapa y con config/departamentos.csv.

let
    Ruta = CarpetaProyecto & "\data\interim\sipsa\sipsa_abastecimiento.csv",

    Origen = Csv.Document(
        File.Contents(Ruta),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]
    ),

    Encabezados = Table.PromoteHeaders(Origen, [PromoteAllScalars = true]),

    Tipos = Table.TransformColumnTypes(
        Encabezados,
        {
            {"art_id", Int64.Type},
            {"articulo", type text},
            {"fuen_id", Int64.Type},
            {"anio", Int64.Type},
            {"mes", Int64.Type},
            {"toneladas", type number},
            {"periodo", Int64.Type},
            {"mercado", type text},
            {"ciudad", type text},
            {"departamento", type text},
            {"dpto_codigo", type text},
            {"producto", type text},
            {"grupo_dane", type text},
            {"en_canasta", type text}
        }
    ),

    // Una fila con cero o sin toneladas no aporta: el mes existe pero no entró
    // nada de ese artículo. Se quitan para no inflar los conteos.
    ConToneladas = Table.SelectRows(Tipos, each [toneladas] <> null and [toneladas] > 0),

    // Total por artículo, departamento y mes. Es la granularidad que usa la app:
    // un departamento puede tener varias centrales (Bogotá llega a 4 en un mes).
    PorDepartamento = Table.Group(
        ConToneladas,
        {"art_id", "articulo", "dpto_codigo", "departamento", "periodo", "anio", "mes"},
        {
            {"toneladas", each List.Sum([toneladas]), type number},
            {"centrales", each Table.RowCount(Table.Distinct(Table.SelectColumns(_, {"mercado"}))), Int64.Type}
        }
    ),

    // Mes anterior en el CALENDARIO, no la fila anterior de la tabla: SIPSA no
    // publicó entre enero de 2021 y enero de 2022, así que la fila anterior
    // puede ser de trece meses antes.
    ConMesAnterior = Table.AddColumn(
        PorDepartamento,
        "periodo_anterior",
        each if [mes] = 1 then [periodo] - 89 else [periodo] - 1,
        Int64.Type
    ),

    // Se une la tabla consigo misma por (artículo, departamento, mes anterior).
    Unida = Table.NestedJoin(
        ConMesAnterior, {"art_id", "dpto_codigo", "periodo_anterior"},
        ConMesAnterior, {"art_id", "dpto_codigo", "periodo"},
        "Anterior", JoinKind.LeftOuter
    ),

    Expandida = Table.ExpandTableColumn(Unida, "Anterior", {"toneladas"}, {"toneladas_antes"}),

    // Variación % de las toneladas. Queda nula cuando no hay mes anterior, y eso
    // es correcto: un hueco se declara, no se rellena con cero.
    ConVariacion = Table.AddColumn(
        Expandida,
        "variacion_toneladas",
        each if [toneladas_antes] = null or [toneladas_antes] = 0 then null
             else ([toneladas] / [toneladas_antes] - 1) * 100,
        type number
    ),

    Final = Table.SelectColumns(
        ConVariacion,
        {"art_id", "articulo", "dpto_codigo", "departamento", "anio", "mes", "periodo",
         "toneladas", "centrales", "toneladas_antes", "variacion_toneladas"}
    ),

    Ordenada = Table.Sort(Final, {{"articulo", Order.Ascending}, {"departamento", Order.Ascending},
                                  {"periodo", Order.Ascending}})
in
    Ordenada
