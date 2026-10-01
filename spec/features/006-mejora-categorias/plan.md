# Plan de implementación – Mejora de la vista de categorías

## 1. Verificación del entorno
- Ejecutar `git status` y `git branch --show-current` para confirmar que estamos en la rama `006-mejora-categorias` y que el árbol está limpio.

## 2. Modificar la vista (`inventario/views.py`)
1. Importar los objetos necesarios:

```python
from django.db.models import Count, Q
```
2. En `categoria_list_crear` sustituir la línea que carga las categorías:

```python
# antes
categorias = Categoria.objects.all()
# después
categorias = Categoria.objects.annotate(
    productos_activos=Count(
        "productos",
        filter=Q(productos__activo=True)
    )
)
```
3. Pasar a la plantilla el atributo `productos_activos` (ya está incluido en cada `cat`).

## 3. Actualizar la plantilla (`inventario/categoria_list.html`)
1. Añadir una nueva columna en el `<thead>`:

```html
<th>Productos</th>
```
2. Dentro del bucle `{% for cat in categorias %}` agregar una celda:

```html
<td>
    <a class="table-link" href="{% url 'producto_list' %}?categoria={{ cat.id }}">
        {{ cat.productos_activos|default:0 }}
    </a>
</td>
```
3. Aplicar clases CSS coherentes con el resto de la tabla (por ejemplo `class="text-center"`).

## 4. Styling (frontend‑design)
- Usar la clase existente para celdas de datos (por ejemplo `class="p-2"`).
- Si no existe una clase específica para enlaces en tabla, crear en `static/css/style.css`:

```css
.table-link {
    color: var(--primary);
    text-decoration: none;
}
.table-link:hover { text-decoration: underline; }
```

## 5. Verificaciones automáticas
1. **Tests unitarios** (`tests/test_categoria_view.py`):
   - Crear categorías y productos reales en la base de datos de test (setUp) y asegurar que `cat.productos_activos` coincide.
   - Verificar que el HTML contiene el enlace correcto con `?categoria=` y el número esperado.
2. **Prueba de query única**:
   - Rodear la llamada a la vista con `assertNumQueries(1)` para certificar que sólo se ejecuta una query.

## 6. Documentación interna
- Añadir un bloque de comentarios en `views.py` explicando el uso de `annotate` y el `related_name` usado.

## 7. Limpieza
- Eliminar imports no usados y cualquier código de depuración.
