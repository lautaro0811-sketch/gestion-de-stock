# 012 · Órdenes de Compra

**Estado:** implementado ✅

## Qué hace

Permite generar órdenes de compra a un proveedor, detallando los productos y cantidades a adquirir junto con el precio de compra pactado. A diferencia de una venta, crear la orden **no modifica el stock**: queda registrada en estado `PENDIENTE` hasta que la mercadería efectivamente llega. En ese momento, desde la misma orden, se puede confirmar la recepción con una acción que **incrementa** el stock de cada producto y cambia el estado a `RECIBIDA`. Una orden pendiente también puede cancelarse si la compra no se concreta.

## Por qué

Refleja cómo funciona una compra real: primero se pacta con el proveedor (se "pide"), y después, en otro momento, llega la mercadería físicamente. Separar ambos pasos evita que el stock se infle con compras que todavía no llegaron al depósito.

## Criterios de aceptación

- [x] Existe el modelo `OrdenCompra`: `proveedor` (FK), `numero_operacion` (único, formato `OC-AÑO-XXXX`, ej. `OC-2026-0001`), `fecha`, `estado` (`PENDIENTE` / `RECIBIDA` / `CANCELADA`), `observacion` (opcional).
- [x] Existe el modelo `OrdenCompraItem`: `orden_compra` (FK), `producto` (FK), `cantidad`, `precio_unitario_compra` (congelado al crear la orden, independiente del `precio_unitario` de venta del producto).
- [x] Al crear una orden de compra (estado inicial `PENDIENTE`), el stock de los productos **no se modifica**.
- [x] El número de operación se asigna de forma atómica, con el mismo criterio ya usado para `Pedido.numero_operacion`, pero con prefijo `OC-` para distinguirlo de los números de venta.
- [x] Existe una acción "Recibir mercadería" disponible solo para órdenes en estado `PENDIENTE`, que genera un movimiento de `ENTRADA` por cada ítem (vía `registrar_entrada`, vinculado a la orden), incrementa el stock real, y cambia el estado a `RECIBIDA`.
- [x] Una orden ya `RECIBIDA` no puede recibirse de nuevo (se evita duplicar el ingreso de stock).
- [x] Existe una acción "Cancelar" disponible solo para órdenes en estado `PENDIENTE`, que cambia el estado a `CANCELADA` sin generar ningún movimiento de stock (porque nunca se descontó nada).
- [x] Una orden `RECIBIDA` o ya `CANCELADA` no puede cancelarse de nuevo.
- [x] No se pueden editar órdenes existentes: solo visualizar, recibir o cancelar (misma regla de inmutabilidad que `Pedido`).
- [x] Los movimientos de `ENTRADA` generados por una recepción muestran en el historial a qué orden de compra pertenecen (`Movimiento.orden_compra`).
- [x] Hay una vista "Órdenes de Compra" en el dashboard: listado con estado, proveedor y número de operación; vista de detalle con los ítems y botones de Recibir/Cancelar según el estado.

## Fuera de alcance

- Generación del PDF de la orden de compra (se aborda en `013-orden-compra-pdf`).
- Reflejar la recepción como egreso en Caja (se aborda en `014-caja-egresos-proveedores`).
- Recepción parcial (recibir solo algunos ítems o cantidades parciales de una orden). Por ahora la recepción es de todo o nada.
- Devolución de mercadería a un proveedor después de haberla recibido. Si una orden ya fue `RECIBIDA`, no puede cancelarse ni revertirse desde este feature.
- Edición de una orden ya creada (cambiar ítems, cantidades o proveedor).