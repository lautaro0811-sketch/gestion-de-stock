# 014 · Caja — Egresos por Compras a Proveedores

**Estado:** propuesta

## Qué hace

Extiende el módulo de Caja (010) para que, al recibir la mercadería de una orden de compra, se registre automáticamente un egreso por el total de la operación. El saldo de Caja pasa a reflejar tanto lo que ingresa por ventas como lo que sale por compras a proveedores.

## Por qué

010-caja ya dejó la estructura preparada para esto ("deja las bases para integrar pagos a proveedores sin reescribir el módulo"). Sin este egreso, el saldo de Caja solo cuenta la mitad de la historia financiera del negocio: lo que entra, pero no lo que sale por reponer stock.

## Criterios de aceptación

- [ ] `MovimientoCaja` tiene un campo `orden_compra` (ForeignKey a `OrdenCompra`, opcional, `on_delete=SET_NULL`, `related_name="movimientos_caja"`), análogo al campo `pedido` ya existente.
- [ ] Al ejecutar `recibir_mercaderia` sobre una orden `PENDIENTE`, además de generar los movimientos de `ENTRADA` de stock, si el total de la orden (suma de `cantidad * precio_unitario_compra` de cada ítem) es mayor que cero se genera un `MovimientoCaja` de tipo `EGRESO` por ese total, con concepto `"Compra - Orden de Compra #<numero_operacion>"` y vinculado a la orden. Si el total es cero, la recepción se completa sin crear un movimiento de caja.
- [ ] `crear_orden_compra` sigue sin generar ningún movimiento de caja (el egreso ocurre recién al recibir, no al crear la orden — mismo criterio que ya se usa para el stock).
- [ ] `cancelar_orden_compra` sigue sin generar ningún movimiento de caja, porque solo puede cancelarse una orden `PENDIENTE`, que nunca generó un egreso.
- [ ] El saldo de Caja (`caja_dashboard`) resta correctamente estos egresos nuevos, sin requerir cambios en la fórmula de cálculo ya existente (suma de ingresos menos suma de egresos).
- [ ] El historial de Caja muestra, para cada egreso de este tipo, a qué orden de compra corresponde.

## Fuera de alcance

- Pagos parciales o a crédito a proveedores (se asume pago contado al momento de recibir la mercadería, igual que el ingreso de una venta se registra al confirmar el pedido).
- Reversión del egreso si una orden ya `RECIBIDA` se "deshace" de alguna forma (no existe ese flujo; ver "Fuera de alcance" de 012-ordenes-compra sobre devoluciones).
- Egresos manuales asociados a un proveedor específico (el egreso manual genérico de 010-caja sigue existiendo tal cual, sin cambios).