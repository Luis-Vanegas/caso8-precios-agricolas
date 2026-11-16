# notebooks/ — los cálculos, paso a paso

| Archivo | Qué es |
|---|---|
| [calculos_paso_a_paso.ipynb](calculos_paso_a_paso.ipynb) | Cada cálculo que reportamos: para qué sirve, la fórmula, un ejemplo a mano con datos reales, la función real y su gráfica |

**El código de los cálculos no está aquí**: está en [`src/indicators/`](../src/indicators/).
El cuaderno lo importa y lo muestra funcionando, así hay una sola versión de cada cálculo.

| Capítulo | Cálculo | Código |
|---|---|---|
| 1 a 3 | Retorno, volatilidad, z-score y alertas | `src/indicators/volatilidad.py` |
| 4 | Correlación con la lluvia (Spearman, con rezago) | `src/indicators/vigilancia.py` |
| 5 | Efecto del clima por eslabón (Pearson, regresión, q-valor) | `src/indicators/sensibilidad.py` |
| 6 | Quiebres (prueba de Chow) | `src/indicators/quiebres.py` |
| 7 | Pronóstico y comparación con el ingenuo | `src/indicators/pronostico.py` |
| 9 | De dónde sale cada cifra del informe y la presentación | — |

## Cómo verlo

- **Sin instalar nada:** ábrelo en GitHub; se ve con todas las tablas y gráficas.
- **Para ejecutarlo** (desde la raíz del proyecto, no necesita internet):

```
.venv\Scripts\python.exe -m jupyter notebook notebooks\calculos_paso_a_paso.ipynb
```

El último capítulo recalcula las tres tablas de resultados y falla si no coinciden con la base.
Si cambias un cálculo en `src/indicators/`, vuelve a correr `scripts\integrar.py` y luego el cuaderno.
