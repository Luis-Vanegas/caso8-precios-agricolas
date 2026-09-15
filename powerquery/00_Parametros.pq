// Parámetro: carpeta raíz del proyecto.
//
// Es lo ÚNICO que hay que cambiar al mover el proyecto de máquina. Todas las
// demás consultas construyen sus rutas a partir de este valor, así que nunca
// se escribe una ruta absoluta dos veces.
//
// Cómo crearlo en Excel:
//   Datos > Obtener datos > Iniciar el editor de Power Query
//   Inicio > Administrar parámetros > Nuevo parámetro
//   Nombre: CarpetaProyecto   Tipo: Texto   Valor actual: la ruta de abajo

"C:\Users\LENOVO\Pictures\AdquiDatos" meta [
    IsParameterQuery = true,
    Type = type text,
    IsParameterQueryRequired = true
]
