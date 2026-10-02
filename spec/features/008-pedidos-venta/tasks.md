# 008 · Pedidos de Venta — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas; marca `[x]` al completarlas._

- [x] Modificar `models.py`: Agregar campo `precio_unitario` (Decimal o Float) al modelo `Producto`.
- [x] Modificar `models.py`: Crear los modelos `Pedido` (FK Cliente, número, estado, timestamps) y `PedidoItem`.
- [x] Modificar `models.py`: Agregar campo `pedido` (ForeignKey, `null=True`, `blank=True`) a `Movimiento`.
- [x] Ejecutar `python manage.py makemigrations` y `python manage.py migrate` para asentar los cambios.
- [x] Modificar `services.py`: Adaptar `registrar_entrada` y `registrar_salida` para recibir un argumento `pedido_id` opcional.
- [x] Modificar `services.py`: Crear lógica `crear_pedido(cliente, items)` asegurando generación de número anual atómico y llamado a salidas de stock.
- [x] Modificar `services.py`: Crear lógica `cancelar_pedido(pedido_id)` ejecutando entradas compensatorias.
- [x] Crear `PedidoForm` e `ItemPedidoFormSet` en `forms.py`.
- [x] Crear vistas `pedido_list`, `pedido_detalle`, `pedido_crear` y `pedido_cancelar` en `views.py`.
- [x] Configurar el ruteo en `urls.py`.
- [x] Desarrollar plantillas HTML: listado de pedidos, detalle de lectura/cancelación, y formulario de alta (con Vanilla JS para agregar filas).
- [x] Modificar `producto_form.html` y listados para exponer visualmente el nuevo `precio_unitario`.
- [x] Actualizar documentación: añadir una nota a `001-catalogo/spec.md` sobre la adición del campo de precio.
- [x] Pruebas locales: confirmar que rechace crear pedidos si no hay stock suficiente, y que la cancelación reintegre correctamente.
- [ ] Validar contra los criterios de aceptación de `spec.md`.
- [ ] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.

## Mantenimiento (checklist recurrente)

- [x] Año nuevo: Asegurar que la lógica del número secuencial reinicie el contador a 0001 al cambiar de año calendario.