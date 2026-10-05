# 012 · Órdenes de Compra — Plan

## Enfoque

Se modela `OrdenCompra`/`OrdenCompraItem` como el espejo de `Pedido`/`PedidoItem`, con una diferencia clave: `crear_orden_compra` **no** llama a ningún servicio de stock (a diferencia de `crear_pedido`, que llama a `registrar_salida` inmediatamente). El movimiento de stock se dispara recién en `recibir_mercaderia`, una función nueva que no tiene equivalente en el flujo de ventas.

## Implementación

1. **Modelos — `inventario/models.py`**:
   - `OrdenCompra`: `proveedor` (FK a `Proveedor`, `on_delete=PROTECT`), `numero_operacion` (CharField, unique=True), `fecha` (default=timezone.now), `estado` (TextChoices: `PENDIENTE`, `RECIBIDA`, `CANCELADA`, default `PENDIENTE`), `observacion` (TextField, blank=True), timestamps.
   - `OrdenCompraItem`: `orden_compra` (FK, on_delete=CASCADE, related_name="items"), `producto` (FK, on_delete=PROTECT), `cantidad` (PositiveIntegerField, MinValueValidator(1)), `precio_unitario_compra` (DecimalField(10,2)). Property `subtotal` igual que `PedidoItem`.
   - Agregar `orden_compra = models.ForeignKey(OrdenCompra, null=True, blank=True, on_delete=SET_NULL, related_name="movimientos")` a `Movimiento`.
2. **Migración**: generar y aplicar.
3. **Servicios — `inventario/services.py`**:
   - `crear_orden_compra(proveedor_id, items_data, observacion="", fecha=None)`: dentro de `transaction.atomic()`, calcular `numero_operacion` con formato `OC-AAAA-NNNN`, siguiendo el criterio de `crear_pedido`: filtrar por prefijo de año, bloquear la última orden de compra del año con `select_for_update()` y verificar colisiones antes de guardar. El Pedido usa `AAAA-NNNN`, por lo que los formatos no colisionan en el mismo año. Crear la orden en `PENDIENTE` y sus ítems. **No llama a `registrar_entrada` ni a ningún servicio de stock.**
   - `recibir_mercaderia(orden_compra_id, usuario=None, fecha=None)`: dentro de `transaction.atomic()`, cargar y bloquear la orden con `select_for_update()`, validar que `estado == PENDIENTE` (si no, `ValidationError`), iterar los ítems llamando a `registrar_entrada` por cada uno con `orden_compra_id` asociado, y cambiar el estado a `RECIBIDA`.
   - `cancelar_orden_compra(orden_compra_id)`: dentro de `transaction.atomic()`, cargar y bloquear la orden con `select_for_update()` y exigir `estado == PENDIENTE` (si no, `ValidationError`; cubre intentar cancelar una ya cancelada o una ya recibida), cambiar el estado a `CANCELADA`. No genera movimientos de stock. `cancelar_pedido` bloquea actualmente la fila y rechaza una orden ya cancelada; la compra además restringe explícitamente la transición al estado pendiente.
   - La firma actual de `registrar_entrada` acepta `pedido_id` opcional, pero no `orden_compra_id`; agregar este último opcional y guardarlo en el movimiento sin alterar las llamadas actuales.
4. **Formularios — `inventario/forms.py`**: `OrdenCompraForm` + formset de ítems, siguiendo la estructura de `PedidoForm`/`ItemPedidoFormSet`.
5. **Vistas — `inventario/views.py`**: `orden_compra_list`, `orden_compra_detalle`, `orden_compra_crear`, `orden_compra_recibir`, `orden_compra_cancelar`.
6. **URLs — `inventario/urls.py`**: rutas nuevas.
7. **Templates**: listado, detalle (con botones Recibir/Cancelar condicionados al estado) y formulario de alta, siguiendo el patrón visual de Pedidos.
8. **Navegación — `templates/base.html`**: link "Órdenes de Compra" en el sidebar.
9. **Admin**: registrar `OrdenCompra` y `OrdenCompraItem`.
10. **Alta rápida de productos**: exponer un endpoint POST AJAX que reutilice `ProductoForm` y habilitar desde el formulario de orden un diálogo `<dialog>` con `fetch()` para crear el producto sin descartar los datos ingresados; agregarlo a los selects de ítems y enfocarlo en un renglón vacío.

## Decisiones

- **Precio de compra separado del precio de venta** — `OrdenCompraItem.precio_unitario_compra` es un campo propio, no reutiliza `Producto.precio_unitario` (que es el precio al que se vende). Evita que registrar una compra pise accidentalmente el precio de venta del catálogo.
- **No reutilizar `registrar_salida`/`registrar_entrada` como orquestador único** — A diferencia de ventas, donde `crear_pedido` llama a stock inmediatamente, acá se separan explícitamente `crear_orden_compra` (sin stock) y `recibir_mercaderia` (con stock), porque son dos momentos de negocio distintos y reales, no un detalle técnico.
- **Cancelación restringida a `PENDIENTE`** — Una orden ya recibida no se puede cancelar desde acá, porque implicaría devolver mercadería al proveedor, un flujo distinto que queda fuera de alcance. El `ValidationError` de `cancelar_orden_compra` cubre también una orden ya cancelada, evitando duplicar el error de doble cancelación que corregimos en `Pedido`.
- **Recepción de todo o nada, sin parcialidad** — Simplifica el modelo de estados (solo 3) y evita la complejidad de "orden parcialmente recibida". Si hace falta en el futuro, es una extensión documentable, no un rediseño.

## Riesgos

- **Confundir el prefijo de número de operación con el de ventas** — Mitigado usando `OC-` como prefijo explícito y verificando en el test que un pedido y una orden de compra creados el mismo año no colisionen en número.
- **Recibir una orden sin stock suficiente en otro lado no aplica acá** — a diferencia de ventas, recibir mercadería siempre *aumenta* stock, así que no hay validación de "stock insuficiente" que replicar en este flujo.