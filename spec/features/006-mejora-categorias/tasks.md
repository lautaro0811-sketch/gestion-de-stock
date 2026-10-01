# Tasks – Mejora de la vista de categorías

| ID | Tarea | Estimado | Estado |
|----|-------|----------|--------|
| T1 | Confirmar entorno: ejecutar `git status` y `git branch --show-current` | 5 min | ☐ |
| T2 | Añadir imports `Count, Q` en `inventario/views.py` | 5 min | ☐ |
| T3 | Reemplazar queryset con `annotate(...productos_activos...)` | 10 min | ☐ |
| T4 | Modificar `categoria_list.html`: nuevo `<th>` y `<td>` con enlace | 15 min | ☐ |
| T5 | Añadir clase CSS `table-link` a `static/css/style.css` (si no existe) | 10 min | ☐ |
| T6 | Escribir tests unitarios para la vista y la plantilla | 20 min | ☐ |
| T7 | Ejecutar `assertNumQueries(1)` en el test que llama a la vista | 10 min | ☐ |
| T8 | Revisar que el número mostrado corresponde a `Categoria.productos.filter(activo=True).count()` | 5 min | ☐ |
| T9 | Limpiar imports y código de depuración | 5 min | ☐ |


> **Nota:** Todas las tareas están en la **Fase A (SPEC)**. No se crea ninguna rama nueva; trabajaremos directamente en la carpeta `006-mejora-categorias`.  Después de tu revisión pasaremos a la fase de implementación.
