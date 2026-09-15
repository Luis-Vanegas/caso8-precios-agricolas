// Base analítica integrada: precio mayorista mensual con su contexto.
//
// Esta es la consulta que produce el entregable de integración. Une SIPSA con
// FAOSTAT, clima y ENSO, y deja marcado en cada fila qué tan válida es la unión.
//
// Decisión de diseño importante: la unión con FAOSTAT es un LEFT JOIN y NUNCA
// descarta filas de SIPSA. Los productos que FAO no publica (cebolla junca,
// chócolo mazorca) siguen en la base con el contexto vacío, porque su serie de
// precios es válida aunque no tenga contraparte internacional.

let
    Base = SipsaMensual,

    // --- Precio al productor de FAOSTAT -------------------------------------
    // Solo la serie anual: la mensual arranca en 2010 y no cubre todos los ítems.
    ProductorAnual = Table.SelectRows(
        FaostatPrecioProductor, each [frecuencia] = "anual"
    ),

    ProductorReducido = Table.SelectColumns(
        ProductorAnual,
        {"item_codigo", "anio", "precio_productor_cop_kg", "es_cifra_oficial"}
    ),

    ConProductor = Table.NestedJoin(
        Base,
        {"item_codigo_fao", "anio"},
        ProductorReducido,
        {"item_codigo", "anio"},
        "fao",
        JoinKind.LeftOuter
    ),

    ExpandirProductor = Table.ExpandTableColumn(
        ConProductor, "fao", {"precio_productor_cop_kg", "es_cifra_oficial"}
    ),

    // La razón entre los dos precios SOLO se calcula donde la correspondencia es
    // exacta. En las agregadas el precio de FAO es una mezcla de varios
    // productos y la razón no significaría nada.
    //
    // OJO: esta razón NO es un margen de intermediación. Los precios de FAO para
    // Colombia son cifra oficial del mismo sistema del DANE que alimenta SIPSA,
    // así que las dos series no son independientes. Ver docs/verificacion_api.md.
    ConRazon = Table.AddColumn(
        ExpandirProductor,
        "razon_mayorista_productor",
        each if [permite_comparar_precio] = true
                and [precio_productor_cop_kg] <> null
                and [precio_productor_cop_kg] > 0
             then Number.Round([precio_cop_kg] / [precio_productor_cop_kg], 3)
             else null,
        type number
    ),

    // --- Fase ENSO del mes ---------------------------------------------------
    EnsoReducido = Table.SelectColumns(Enso, {"anio", "mes", "fase", "anomalia"}),

    ConEnso = Table.NestedJoin(
        ConRazon, {"anio", "mes"}, EnsoReducido, {"anio", "mes"}, "enso", JoinKind.LeftOuter
    ),

    ExpandirEnso = Table.ExpandTableColumn(
        ConEnso, "enso", {"fase", "anomalia"}, {"fase_enso", "anomalia_enso"}
    ),

    // --- Anomalía climática de la zona productora ----------------------------
    //
    // ATENCIÓN: el cruce va POR EL PUENTE, no directo sobre `producto`.
    //
    // La configuración de zonas dice "Papa"; SIPSA dice "Papa negra*". Unir
    // directo sobre el nombre del producto corre sin error y devuelve CERO
    // filas: un join vacío no se queja. El puente traduce entre los dos
    // vocabularios y además resuelve que una zona sirva a varios productos.
    ZonaPorProducto = Table.NestedJoin(
        ExpandirEnso,
        {"producto"},
        ZonasPuente,
        {"producto_sipsa"},
        "zona",
        JoinKind.LeftOuter
    ),

    ExpandirZona = Table.ExpandTableColumn(
        ZonaPorProducto, "zona", {"producto_zona", "departamento"}
    ),

    ClimaReducido = Table.SelectColumns(
        Clima, {"producto", "departamento", "anio", "mes", "precipitacion_anomalia"}
    ),

    ConClima = Table.NestedJoin(
        ExpandirZona,
        {"producto_zona", "departamento", "anio", "mes"},
        ClimaReducido,
        {"producto", "departamento", "anio", "mes"},
        "clima",
        JoinKind.LeftOuter
    ),

    ExpandirClima = Table.ExpandTableColumn(ConClima, "clima", {"precipitacion_anomalia"}),

    // Un producto con dos zonas produce dos filas por mes. Se promedia para
    // volver a una fila por mercado, producto y mes.
    Final = Table.Group(
        ExpandirClima,
        {"mercado", "producto", "periodo"},
        {
            {"datos", each Table.FirstN(Table.RemoveColumns(_, {"precipitacion_anomalia"}), 1), type table},
            {"precipitacion_anomalia", each List.Average(List.RemoveNulls([precipitacion_anomalia])), type number}
        }
    )
in
    Final
