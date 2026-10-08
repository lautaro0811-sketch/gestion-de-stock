# 008 · Pedidos de Venta

**Estado:** implementado ✅

## Qué hace

Permite registrar ventas a clientes generando un "Pedido". Al crearse, el sistema descuenta automáticamente el stock de los productos seleccionados y genera un número de operación correlativo anual (ej. 2026-0001) para presentarlo de forma profesional. Cada ítem del pedido congela el precio unitario del producto al momento exacto de la venta para que futuros cambios en el catálogo no alteren el valor histórico. Si un pedido se cancela, el sistema devuelve la mercadería al inventario automáticamente.

## Por qué

Es el motor transaccional comercial del sistema. Sustituye la necesidad de cargar "Salidas" manuales por cada venta, agrupando múltiples artículos bajo un mismo comprobante y cliente, garantizando que el stock y los precios históricos queden resguardados y auditables.

## Criterios de aceptación

_Condiciones verificables que deben cumplirse para dar la feature por terminada. Redacta cada una de forma que se pueda comprobar con un sí/no. Marca `[x]` al cumplirse._

- [x] El modelo `Producto` incluye ahora un campo `precio_unitario`.
- [x] Se pueden crear Pedidos (estado `CONFIRMADO`) con un Cliente opcional y agregando múltiples ítems (producto, cantidad). Si no se selecciona uno, se guarda el nombre del comprador o `"Consumidor Final"` en el snapshot.
- [x] Al guardar un Pedido, se le asigna de manera segura un número de operación con formato `AÑO-XXXX` (ej. 2026-0001).
- [x] Cada ítem del pedido copia y congela el `precio_unitario` del catálogo y calcula su subtotal.
- [x] La creación del pedido dispara internamente movimientos de tipo `SALIDA` para cada ítem, vinculados al pedido.
- [x] No se pueden editar pedidos existentes: la inmutabilidad rige. Solo se pueden visualizar o cancelar.
- [x] Al cancelar un pedido, su estado cambia a `CANCELADO` y se generan movimientos compensatorios de `ENTRADA` por cada ítem.
- [x] Los movimientos en el historial general de stock (`002-movimientos`) muestran a qué número de pedido pertenecen si corresponden a una venta o cancelación.

## Fuera de alcance

_Lo que esta feature NO incluye, para evitar que crezca. Si algo se difiere, enlaza a dónde (roadmap/backlog)._

- Generación del PDF del pedido (se abordará en `009-pedido-pdf`).
- Registro de los ingresos de dinero, cobros o manejo de "Caja" (se abordará en `010-caja`).
- Alta de Clientes integrada dentro del formulario de venta; la feature 015 agrega un enlace al alta existente en una pestaña nueva.

## Nota de integración (015)

La feature de integración permite ventas sin Cliente registrado, preservando los snapshots del comprador y manteniendo stock, correlativo, cancelación y caja por el mismo flujo de `crear_pedido`.