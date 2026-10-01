# Mejora de la vista de categorías

## Descripción
Ampliar la tabla de categorías (`inventario/categoria_list.html`) para que muestre, junto al nombre, la **cantidad de productos activos** asociados a cada categoría.  
El número debe ser un **enlace** que lleva al listado de productos (`inventario/producto_list.html`) filtrado por esa categoría mediante el parámetro GET `categoria`.

## Acceptance Criteria (verificables)

| # | Criterio | Verificación |
|---|----------|--------------|
| 1 | La tabla incluye una columna **“Productos”** con el conteo de productos activos por categoría. | Revisar el HTML generado y buscar `<th>Productos</th>` y `<td>` con un número entero. |
| 2 | Cada número es un enlace que apunta a `producto_list` con `?categoria=<id>`. | El `href` del enlace debe ser `{% url 'producto_list' %}?categoria={{ cat.id }}` y la página resultante muestra solo los productos de esa categoría. |
| 3 | El conteo se obtiene con **una sola query** usando `annotate(Count(...))`. | Ejecutar `assertNumQueries(1)` en el test que llama a la vista y confirmar que no hay N+1 consultas. |
| 4 | No se crea ni modifica lógica de negocio en los modelos. | No se añaden métodos ni campos nuevos a `Categoria` o `Producto`. |
| 5 | Sólo se listan **productos activos** (`activo=True`). | El número coincide con `Categoria.productos.filter(activo=True).count()`. |
| 6 | El link lleva a la vista de inventario (`producto_list`) ya existente y respeta el filtro `categoria`. | Al hacer click, la tabla de productos muestra exclusivamente los de la categoría seleccionada. |

## Fuera de alcance (posibles features futuras)

- Edición / borrado de categorías desde esta tabla.  
- Mensaje de error personalizado al intentar borrar una categoría con productos asociados. 

---

## Supuestos

| Elemento | Valor verificado en el código |
|----------|------------------------------|
| **Template** | `inventario/categoria_list.html` (confirmado en `views.py`). |
| **Vista** | `categoria_list_crear` (renderiza `categoria_list.html`). |
| **Nombre de la vista de productos** | `producto_list` (usada en `url` y en la plantilla `producto_list.html`). |
| **Related name** | `Categoria` → `productos` (`related_name="productos"` en `inventario/models.py` – **línea 25**). |
| **Campo “activo”** | `Producto.activo` (`BooleanField`). |
| **Parámetro GET** | `categoria` ya aceptado por `producto_list` (líneas 25‑27 de `views.py`). |

## Restricciones de tech‑stack

- No usar frameworks CSS/JS externos ni CDNs.  
- No colocar estilos en línea; usar clases de `static/css/style.css`.  
- Consultar la skill **frontend‑design** para decisiones visuales manteniendo la identidad existente.
