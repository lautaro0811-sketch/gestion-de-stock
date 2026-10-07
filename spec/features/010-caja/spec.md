# 010 · Caja y Flujo de Efectivo

**Estado:** Hecho ✅

## Qué hace

Implementa un módulo de "Caja" que centraliza el flujo de dinero del sistema. Registra automáticamente los ingresos generados por los Pedidos de Venta y permite al usuario registrar Egresos manuales (como gastos diarios, viáticos o limpieza). Muestra el saldo actual disponible en tiempo real y un historial detallado de movimientos.

## Por qué

Permite al usuario llevar un control financiero básico (arqueo de caja) que va de la mano con el control de inventario. Al dejar la estructura de la base de datos abierta (desacoplada de las ventas), sienta las bases técnicas para integrar en el futuro los pagos a proveedores sin tener que reescribir el módulo.

## Criterios de aceptación

_Condiciones verificables que deben cumplirse para dar la feature por terminada. Redacta cada una de forma que se pueda comprobar con un sí/no. Marca `[x]` al cumplirse._

- [x] El modelo `MovimientoCaja` se crea exitosamente en la base de datos utilizando campos decimales para evitar errores de redondeo.
- [x] La estructura permite registrar un movimiento sin estar obligado a vincularlo a un pedido de venta (clave foránea opcional).
- [x] Al "Confirmar" un Pedido de Venta, el sistema genera automáticamente un movimiento de **INGRESO** en la caja por el total de la operación.
- [x] Al "Cancelar" un Pedido, se genera automáticamente un movimiento de **EGRESO** compensatorio por el mismo valor para revertir el ingreso.
- [x] Existe un formulario de "Nuevo Egreso Manual" para que el usuario registre salidas de dinero operativas, con un campo para describir el concepto.
- [x] El Dashboard de Caja muestra el saldo exacto en tiempo real sin usar campos estáticos desincronizables.
- [x] Los templates HTML de esta feature no contienen atributos `style="..."` en línea, respetando estrictamente el archivo `style.css` global[cite: 11].

## Fuera de alcance

- Registro de compras formales a proveedores y manejo de cuentas corrientes (será una feature futura, aunque este módulo la deja preparada).
- Nota de extensión: el vínculo opcional de `MovimientoCaja` con `OrdenCompra` y el egreso automático al recibir mercadería se incorporaron en `014-caja-egresos-proveedores`.
- Manejo de múltiples cajas o sucursales (habrá una única caja general).
- Múltiples medios de pago (tarjeta, transferencia); por ahora, el saldo se maneja como una caja unificada de efectivo.