# 015 · Integración del Flujo Operativo — Plan

## Enfoque

No se agrega ningún modelo nuevo. Se ajustan modelos, formularios, servicios y templates ya existentes (`Pedido`, `PedidoForm`, `crear_pedido`, `producto_list.html`, `pedido_form.html`) para cerrar las tres inconsistencias detectadas. El mecanismo de snapshot (`cliente_nombre`, `cliente_tipo_documento`, `cliente_numero_documento`, `cliente_telefono`, ya implementado en la migración `0009`) se reutiliza tal cual está, sin modificarlo, para resolver el caso de consumidor final.

## Implementación

1. **Verificación previa (antes de tocar código)**: la búsqueda encontró accesos directos en `pedido_list.html` (`nombre`, tipo y número de documento), `pedido_confirm_cancel.html` (`nombre`) y `Pedido.__str__` (`nombre`). Se reemplazan por snapshots y un fallback seguro. `caja_dashboard.html` no accede a campos del cliente; solo muestra el número de operación de `movimiento.pedido`.
2. **Modelo — `inventario/models.py`**: cambiar `Pedido.cliente` a `on_delete=models.PROTECT, null=True, blank=True`.
3. **Migración**: generar y aplicar (campo ya existente, solo cambia nullability — no requiere migración de datos).
4. **Formulario — `inventario/forms.py`**: en `PedidoForm`, quitar `required=True` del campo `cliente`; agregar un campo nuevo `nombre_comprador` (CharField, opcional, no es parte del modelo `Pedido` directamente si se maneja como campo de formulario no-modelo, o se pasa aparte a la vista).
5. **Servicio — `inventario/services.py`**: modificar `crear_pedido` para aceptar `cliente_id: int | None` y un parámetro nuevo `nombre_comprador: str = ""`. Si `cliente_id` es `None`: no buscar ningún `Cliente`, `pedido.cliente = None`, y completar `cliente_nombre = nombre_comprador or "Consumidor Final"`, dejando los demás campos de snapshot vacíos. Si `cliente_id` tiene valor, mantener el comportamiento actual (snapshot copiado del `Cliente`).
6. **Vista — `inventario/views.py`**: ajustar `pedido_crear` para pasar `cliente_id=None` cuando no se seleccionó cliente, y el nuevo `nombre_comprador` del formulario a `crear_pedido`.
7. **Botón "-Salida" — `templates/inventario/producto_list.html`**: cambiar el link para que apunte a `pedido_crear` con el `producto_id` por GET. La vista inicializa la fila extra del `ItemPedidoFormSet` con el producto activo recibido; el mecanismo actual de Vanilla JS enlaza esa fila y actualiza stock/precio/subtotal al cargar, sin parsear parámetros en JavaScript.
8. **Botón "+Entrada"**: solo cambiar el texto visible/tooltip, sin tocar la URL ni la vista `movimiento_crear`.
9. **"+ Nuevo Cliente" en Nueva Venta — `templates/inventario/pedido_form.html`**: agregar un link que abra la vista `cliente_list_crear` (URL `cliente_list`) en una pestaña nueva (`target="_blank"`), como acceso rápido. El patrón existente de Órdenes de Compra crea productos mediante un diálogo AJAX; no se replica ese mecanismo porque el requisito de cliente pide abrir el alta existente en otra pestaña.
10. **Documentación**: agregar una nota de extensión breve en `spec/features/005-mejora-inventario/spec.md` y en los archivos existentes `spect.md` de `007-clientes`, `008-pedidos-venta` y `009-pedido-pdf`. Estos tres archivos se llaman `spect.md` en el repositorio; no se crea ni renombra documentación.

## Decisiones

- **Reutilizar el snapshot existente en vez de crear un cliente genérico "Consumidor Final"** — Al confirmarse que `cliente_nombre` y los demás campos de snapshot ya existen, ya se completan en cada venta y ya se muestran en los templates, esta es la solución de menor superficie: no requiere seed de datos ni registros ficticios en `Cliente`.
- **"-Salida" se convierte en atajo a "Nueva Venta", no se elimina** — Eliminarlo quitaría una conveniencia real (empezar una venta con un clic desde Inventario). Redirigir con el producto precargado mantiene la velocidad sin bypassear el flujo formal.
- **"+Entrada" se mantiene sin cambios de fondo** — Hay casos legítimos de corrección manual de stock que no son una compra a proveedor (hallazgo de un sobrante, corrección de un error de carga). Solo se aclara su propósito para que no se use como atajo de reposición informal.
- **No se renombra Pedido → Venta** — Documentado en "Fuera de alcance" de spec.md.

## Riesgos

- **Precarga del producto** — La fila extra inicial se renderiza desde el formset Django y el JS existente la enlaza al cargar; no hace falta modificar el mecanismo para agregar filas.
- **Accesos directos al cliente** — Confirmados en `pedido_list.html`, `pedido_confirm_cancel.html` y `Pedido.__str__`; usar snapshots y el fallback `"Consumidor Final"` evita dereferenciar la relación nula.