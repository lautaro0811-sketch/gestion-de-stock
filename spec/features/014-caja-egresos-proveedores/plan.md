# 014 · Caja — Egresos por Compras a Proveedores — Plan

## Enfoque

Se extiende `MovimientoCaja` con un campo `orden_compra` opcional, simétrico a `pedido`. La generación del egreso se agrega dentro de `recibir_mercaderia` (inventario/services.py), reutilizando `registrar_egreso_caja` que ya existe (la misma función que usa `cancelar_pedido` para el egreso compensatorio de ventas), sin crear una función nueva.

## Implementación

1. **Modelo — `inventario/models.py`**: agregar `orden_compra = models.ForeignKey(OrdenCompra, null=True, blank=True, on_delete=models.SET_NULL, related_name="movimientos_caja")` a `MovimientoCaja`.
2. **Migración**: generar y aplicar.
3. **Servicio — `inventario/services.py`**: dentro de `recibir_mercaderia`, después de iterar los ítems y llamar a `registrar_entrada` por cada uno, calcular el total de la orden (`sum(item.cantidad * item.precio_unitario_compra for item in orden.items.all())`) y llamar a `registrar_egreso_caja(monto=total, concepto=f"Compra - Orden de Compra #{orden.numero_operacion}", orden_compra=orden)`. Verificar primero la firma actual de `registrar_egreso_caja` (hoy solo recibe `pedido` como vínculo opcional, según lo visto en 010) y extenderla para aceptar también `orden_compra` opcional, sin romper las llamadas existentes desde `cancelar_pedido`.
4. **Documentación**: agregar una nota breve en `spec/features/010-caja/spec.md` (sección "Fuera de alcance" o una nueva nota al pie) indicando que el campo `orden_compra` y la integración con egresos por compras fueron añadidos por `014-caja-egresos-proveedores`, siguiendo el mismo criterio ya usado para documentar extensiones retroactivas (como `precio_unitario` en 001).

## Decisiones

- **Reutilizar `registrar_egreso_caja` en vez de crear una función nueva** — Es exactamente el mismo tipo de operación (registrar una salida de dinero con un concepto y una referencia opcional), solo cambia qué modelo se referencia. Extender la firma es más simple y consistente que duplicar la lógica.
- **Egreso al recibir, no al crear la orden** — Ya fue decidido y documentado en 012; acá solo se respeta esa decisión para que caja y stock se muevan en el mismo momento.
- **Sin compensación en cancelación** — No hace falta, porque `cancelar_orden_compra` solo opera sobre órdenes `PENDIENTE`, donde nunca se generó un egreso.
- **Total de compra cero** — Se recibe la orden sin crear un movimiento de caja, ya que los egresos de caja requieren un monto positivo y un movimiento por cero no cambia el saldo.

## Riesgos

- **Olvidar envolver el nuevo egreso en la misma transacción atómica de `recibir_mercaderia`** — Si el egreso de caja quedara fuera de `transaction.atomic()`, una falla a mitad de camino podría dejar el stock actualizado sin el egreso registrado (o viceversa). Mitigación: verificar explícitamente que la llamada a `registrar_egreso_caja` quede dentro del mismo bloque atómico que ya envuelve `recibir_mercaderia`.