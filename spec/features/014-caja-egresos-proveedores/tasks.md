# 014 · Caja — Egresos por Compras a Proveedores — Tareas

- [x] Confirmar contra el código real la firma actual de registrar_egreso_caja en inventario/services.py antes de extenderla.
- [x] Agregar el campo orden_compra a MovimientoCaja.
- [x] Generar y aplicar la migración.
- [x] Extender registrar_egreso_caja para aceptar orden_compra opcional, sin romper las llamadas existentes desde cancelar_pedido.
- [x] Modificar recibir_mercaderia para calcular el total de la orden y llamar a registrar_egreso_caja, dentro del mismo transaction.atomic.
- [x] Agregar la nota de extensión en spec/features/010-caja/spec.md.
- [x] En el detalle de la orden, mostrar una etiqueta visual distinta si el total es $0.00, sin bloquear la recepción.
- [ ] Tests: recibir una orden de compra genera un MovimientoCaja de tipo EGRESO por el monto correcto; el egreso queda vinculado a la orden_compra; crear_orden_compra NO genera ningún movimiento de caja; cancelar_orden_compra NO genera ningún movimiento de caja; el saldo de caja_dashboard refleja correctamente un escenario combinado de ventas (ingresos) y compras recibidas (egresos); si recibir_mercaderia falla a mitad de camino (por ejemplo, un producto que ya no existe), ni el stock ni el egreso de caja quedan aplicados parcialmente (rollback completo); una orden con total cero se recibe sin generar movimiento de caja y se muestra su etiqueta visual.
- [ ] Correr python manage.py test (suite completa) y confirmar que todo pasa.
- [ ] Validar contra los criterios de aceptación de spec.md.
- [ ] Mover la feature a "Hecho" en ../../constitution/roadmap.md.