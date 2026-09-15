# Guion de presentación — Caso 8

Doce minutos. La app corriendo en local como respaldo, abierta unos minutos antes si vas a usar
la versión publicada, porque Streamlit Community Cloud duerme la app por inactividad.

---

## Minuto 0–2 — El problema, con un número

Abrí con el dato, no con la definición.

> "El limón Tahití en Colombia tiene una volatilidad anualizada del 135 %. Una sola serie de
> precio en Bogotá va de 698 a 6 075 pesos por kilo. Casi nueve veces. Ningún activo financiero
> se mueve así."

Después el problema real: la información existe, pero llega tarde y dispersa. El DANE publica
todos los días, FAO una vez al año, la NOAA cada mes. Nadie los junta.

**Mostrar:** página principal de la app, con las alertas del último mes.

## Minuto 2–4 — Las cinco fuentes y las tres herramientas

Tabla de fuentes con su rol y frecuencia. El punto a dejar claro:

> "La detección temprana sale de SIPSA porque publica a diario. FAOSTAT publica una vez al año
> con un año de rezago: no puede detectar nada temprano. Aporta el contexto, no la señal."

Las tres herramientas del reto y qué hace cada una: Python de crudo a intermedio, OpenRefine
homologa, Power Query integra.

**Mostrar:** la tabla de fuentes de la página principal.

## Minuto 4–7 — Lo que encontramos verificando

Esta es la parte fuerte. Tres historias cortas, una por diapositiva.

**Uno: la documentación mentía.** La guía del DANE de 2020 declara un endpoint HTTP que no
procesa SOAP: responde una página HTML a cualquier petición. Por HTTPS sí funciona, y el binding
es SOAP 1.2, no 1.1. Eso no está escrito en ningún lado.

**Dos: el número grande mentía.** El chequeo de inconsistencias de comercio arrojó 2 730 casos.
Abrí el primero: era `Fruit` con producción cero. `Fruit` no es un cultivo, es un agregado de
grupo. Filtrando bien quedaron 97, y de esos solo 9 son inconsistencias reales.

> "De 2 730 a 9. La diferencia fue abrir el dato en vez de confiar en el agregado."

**Tres: el código correcto mentía.** El cruce de clima con precios unía cero filas de 33 977.
Corría sin un solo error. La configuración decía "Papa" y SIPSA dice "Papa negra". Un join que no
encuentra nada no se queja.

> "Ese es el error más peligroso: el que no falla."

## Minuto 7–9 — El hallazgo que cambió el diseño

> "Nos propusimos cruzar SIPSA con FAOSTAT producto a producto. No se puede."

La tabla de correspondencias: 13 exactas, 10 agregadas, 8 genéricas, 2 sin equivalente.

El ejemplo concreto: guayaba y mango tommy comparten el ítem 571 de FAO. El precio de ese ítem
no es el de ninguno de los dos.

> "Si calculás un margen contra ese precio, te da un número razonable y es falso."

Y la verificación que cierra el tema: buscamos "Passion fruit", "Lulo", "Granadilla" y "Tree
tomato" en los tres dominios de FAOSTAT. No existen. No es un problema de acceso que otra API
resuelva, es el límite de una clasificación internacional que no contempla productos andinos.

Por eso el modelo tiene dos dimensiones de producto unidas por un puente que declara, fila por
fila, qué tan válida es la correspondencia.

**Mostrar:** página "Calidad de datos", tabla de ítems que reciben varios productos.

## Minuto 9–11 — La app

Recorrido rápido, sin detenerse en lo obvio.

1. **Semáforo.** El umbral y de dónde sale. Decir en voz alta que son convenciones de este
   trabajo, no estándares oficiales.
2. **Detalle por producto.** Elegí uno con correspondencia agregada, por ejemplo guayaba, y
   mostrá la advertencia que emite la app.
3. **Calidad de datos.** Las siete limitaciones declaradas.

> "La limitación viaja con el dato. No está escondida en un anexo: la app te avisa en la cara
> cuando la comparación no es válida."

## Minuto 11–12 — Fortalezas, debilidades y cierre

**Fortalezas.** Cinco supuestos de la documentación resultaron falsos y se corrigieron contra el
servicio real. Idempotencia probada. 75 tests sin red. 19 chequeos de integridad, tres nacidos de
un error real.

**Debilidades, dichas sin adornos.** La API de FAOSTAT quedó sin verificar por falta de token.
Las zonas productoras son capitales departamentales usadas como aproximación. SIPSA arranca en
2020 en el servicio web. Solo 13 de 33 productos admiten comparación entre fuentes. Y lo más
importante: **no está comprobado que las alertas anticipen crisis de abastecimiento**; detectan
movimientos estadísticamente anómalos, que es otra cosa.

Cierre:

> "El entregable no es el dashboard. Es saber exactamente qué se puede y qué no se puede concluir
> con estos datos, y haberlo dejado escrito en el código, en la base y en la pantalla."

---

## Preguntas que te van a hacer

**¿Por qué no usaron la API de FAOSTAT?**
Exige token y no lo conseguimos a tiempo. La carga histórica sale de las descargas masivas, que
no piden credenciales, así que no bloquea nada. El módulo está escrito y marcado con lo que falta
verificar.

**¿Por qué DuckDB y no Postgres?**
Archivo único sin servidor, lee Parquet directo, y se versiona en el repositorio. La app en
Streamlit Community Cloud lo lee sin credenciales. Un servidor solo se justificaría si
necesitáramos actualización automática en la nube.

**¿Los umbrales de alerta de dónde salen?**
Son convenciones de este trabajo: 2 y 3 desviaciones estándar. No son estándares oficiales y está
dicho en la app y en el reporte. Calibrarlos requiere una lista de eventos conocidos.

**¿Por qué no calculan el margen entre precio mayorista y precio al productor?**
Porque las dos series no son independientes. Los 6 893 registros de precio al productor de
Colombia en FAOSTAT llevan flag de cifra oficial, o sea que vienen del gobierno colombiano,
probablemente del mismo sistema del DANE que alimenta SIPSA. Restar una de otra no mide
intermediación.

**¿Qué harían con más tiempo?**
Tres cosas, en este orden. Validar las alertas contra eventos conocidos de abastecimiento.
Refinar las zonas productoras con polígonos de UPRA en vez de capitales departamentales. Y sumar
los microdatos del DANE de 2013 a 2019 para extender la historia de precios.
