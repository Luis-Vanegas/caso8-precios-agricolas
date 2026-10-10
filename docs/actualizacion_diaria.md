# Actualización diaria

Un solo comando corre la cadena completa: **descargar → limpiar → integrar**.

```
.venv\Scripts\python.exe scripts\diario.py
```

**Cerrar la app antes**: si Streamlit está abierta, Windows bloquea la base y la integración falla.

## Qué hace cada paso

| Paso | Script | Si falla |
|---|---|---|
| 1. Descargar lo nuevo | `actualizar.py` (10 fuentes) | **Se sigue**: la limpieza usa la última descarga buena de esa fuente |
| 2. Limpiar | `preparar.py` | Se detiene: integrar con una limpieza rota dejaría la base a medio armar |
| 3. Integrar | `integrar.py` (modelo, 29 chequeos e indicadores) | Se detiene y devuelve error |

Devuelve `0` si todo salió bien y `1` si algo falló.

## Por qué conviene correrlo todos los días

- **Precios semanales de SIPSA**: el servicio solo entrega las últimas ~51 semanas. La historia se arma guardando cada descarga en `data/raw/sipsa_semanal/<fecha>/`. Si un día no se corre, no se pierde nada mientras se corra al menos una vez cada 12 meses, pero cuanto más seguido, más rápido se ven las semanas nuevas.
- **Clima de Open-Meteo**: el pronóstico a 16 días y el estacional cambian a diario.
- **SIPSA diario**: publica precios cada día hábil.

## Programarlo en Windows (lo crea cada persona en su equipo)

Desde PowerShell. Crea una tarea que corre todos los días a las 6:00 a. m. y guarda la salida en `data/diario.log`. **Cambiar la ruta** si el proyecto está en otra carpeta (la tarea arranca en `C:\Windows\System32`, por eso la ruta va completa):

```
schtasks /Create /SC DAILY /ST 06:00 /TN "Caso8 actualizacion diaria" /TR "cmd /c cd /d C:\Users\LENOVO\Pictures\AdquiDatos && .venv\Scripts\python.exe scripts\diario.py >> data\diario.log 2>&1"
```

Para ver si corrió: abrir `data/diario.log`. Para quitarla:

```
schtasks /Delete /TN "Caso8 actualizacion diaria" /F
```

La tarea solo corre si el computador está encendido a esa hora.
