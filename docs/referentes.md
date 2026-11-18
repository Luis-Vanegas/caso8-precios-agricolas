# Referentes: herramientas reales de monitoreo de precios

Revisados el 2026-11-17. Sirven para comparar el proyecto con lo que ya existe y justificar decisiones de diseño. **No** se copian sus datos.

| Herramienta | Quién | Qué hace | Qué tomamos para este proyecto |
|---|---|---|---|
| [FPMA Tool](https://www.fao.org/giews/food-prices/price-tool/es/) | FAO (GIEWS) | Plataforma web para consultar y analizar precios de alimentos de más de 90 países. Calcula el indicador ODS 2.c.1, que cuenta las anomalías de precio de cada serie. | La idea de medir si un precio es **anómalo frente a su propia historia**, que es lo que hace nuestro semáforo (`src/indicators/volatilidad.py`). Nuestra fórmula no es la oficial del ODS 2.c.1: es un z-score sobre retornos mensuales. |
| [Economic Explorer](https://dataviz.vam.wfp.org/economic_explorer/prices) ([datos en HDX](https://data.humdata.org/dataset/global-wfp-food-prices)) | Programa Mundial de Alimentos (WFP) | Muestra y permite descargar precios de alimentos por país y mercado, mes a mes. | Ver un producto en un mercado a lo largo del tiempo, y comparar mercados. Es la base de "La historia de un alimento". |
| [SIPSA](https://www.dane.gov.co/index.php/estadisticas-por-tema/economia/precios-y-costos/sistema-de-informacion-de-precios-y-abastecimiento-del-sector-agropecuario-sipsa) | DANE | Precios mayoristas, abastecimiento e insumos del sector agropecuario de Colombia. Publica boletines. | Es nuestra fuente principal. Sus boletines comparan cada periodo con el mismo periodo del año anterior; por eso el tablero trae el semáforo "frente a hace un año". |

## Lo que agregamos y no traen esos referentes

- **Pronóstico puesto a prueba**: se muestra en cuántos productos el modelo le gana a "el precio sigue igual" y en cuántos no.
- **Estacionalidad**: en qué meses suele estar más barato cada alimento.
- **Cruce con clima a nivel de zona de cultivo** (IDEAM y NASA POWER), con corrección por pruebas múltiples (q-valor).
- **Lo internacional conectado con lo nacional**: qué parte se importa (FAO) y fertilizantes (Banco Mundial) frente al precio de la comida (SIPSA).
