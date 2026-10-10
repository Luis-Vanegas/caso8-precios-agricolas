"""Secciones de las paginas fusionadas.

Antes cada una era una pagina aparte. Para pasar de 14 a 7 paginas se juntaron:
el codigo de cada antigua pagina vive aqui como una funcion `mostrar()`, y la
pagina que la absorbe la llama dentro de una pestana. Un `return` dentro de
`mostrar()` corta solo esa seccion, no la pagina entera (st.stop() si la cortaria).
"""
