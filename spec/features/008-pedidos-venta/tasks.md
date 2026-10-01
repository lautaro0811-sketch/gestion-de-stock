# 008 · Pedidos de Venta — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas; marca `[x]` al completarlas._

- [ ] Modificar `models.py`: Agregar campo `precio_unitario` (Decimal o Float) al modelo `Producto`.
- [ ] Modificar `models.py`: Crear los modelos `Pedido` (FK Cliente, número, estado, timestamps) y `PedidoItem`.
- [ ] Modificar `models.py`: Agregar campo `pedido` (ForeignKey, `null=True`, `blank=True`) a `Movimiento`.
- [ ] Ejecutar `python manage.py makemigrations` y `python manage.py migrate` para asentar los cambios.
- [ ] Modificar `services.py`: Adaptar `registrar_entrada` y `registrar_salida` para recibir un argumento `pedido_id` opcional.
- [ ] Modificar `services.py`: Crear lógica `crear_pedido(cliente, items)` asegurando generación de número anual atómico y llamado a salidas de stock.
- [ ] Modificar `services.py`: Crear lógica `cancelar_pedido(pedido_id)` ejecutando entradas compensatorias.
- [ ] Crear `PedidoForm` e `ItemPedidoFormSet` en `forms.py`.
- [ ] Crear vistas `pedido_list`, `pedido_detalle`, `pedido_crear` y `pedido_cancelar` en `views.py`.
- [ ] Configurar el ruteo en `urls.py`.
- [ ] Desarrollar plantillas HTML: listado de pedidos, detalle de lectura/cancelación, y formulario de alta (con Vanilla JS para agregar filas).
- [ ] Modificar `producto_form.html` y listados para exponer visualmente el nuevo `precio_unitario`.
- [ ] Actualizar documentación: añadir una nota a `001-catalogo/spec.md` sobre la adición del campo de precio.
- [ ] Pruebas locales: confirmar que rechace crear pedidos si no hay stock suficiente, y que la cancelación reintegre correctamente.
- [ ] Validar contra los criterios de aceptación de `spec.md`.
- [ ] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.

## Mantenimiento (checklist recurrente)

- [ ] Año nuevo: Asegurar que la lógica del número secuencial reinicie el contador a 0001 al cambiar de año calendario.