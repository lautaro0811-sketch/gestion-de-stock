# 005 · Mejora Inventario — Tareas

- [ ] Implementar exportación CSV respetando los filtros de búsqueda, categoría y "solo alertas".
- [ ] Añadir botones **+Entrada** y **‑Salida** por fila que generen la URL correcta a `movimiento_crear` con los parámetros `producto` y `tipo`.
- [ ] Implementar ordenamiento de la tabla mediante query‑params `orden` y `dir`, con whitelist de campos y visualización de la flecha de dirección.
- [ ] Modificar la vista `movimiento_crear` para leer los parámetros GET `producto` y `tipo`, envolver la conversión de `producto` a entero en `try/except` y pasar esos valores como `initial` al formulario.
- [ ] Migrar los estilos en línea (`style="..."`) de los templates a clases en `static/css/style.css` (tarea pendiente del feature 003‑dashboard).
