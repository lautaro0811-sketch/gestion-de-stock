# 015 · Integración del Flujo Operativo

**Estado:** completado ✅

## Qué hace

Corrige tres puntos de fricción e inconsistencia detectados al revisar el flujo completo de venta, acumulados a través de los features 005, 007, 008 y 009 implementados por separado:

1. El botón rápido "-Salida" en Inventario permitía descontar stock como si fuera una venta, sin pasar por `crear_pedido`: sin cliente, sin número de operación, sin remito en PDF y sin que se registrara el ingreso en Caja. Pasa a redirigir a "Nueva Venta" con el producto ya precargado, en vez de descontar stock por su cuenta.
2. "Nueva Venta" no ofrece forma de registrar un cliente nuevo sin salir de la pantalla, a diferencia de Órdenes de Compra (que sí permite crear un producto al vuelo).
3. Registrar una venta exige seleccionar un `Cliente` ya dado de alta, lo cual es fricción innecesaria para el caso más frecuente de un local de productos de limpieza: el consumidor final de mostrador, que no quiere dar su DNI para comprar un detergente.

## Por qué

Cada uno de estos puntos fue razonable en el momento en que se implementó su feature de origen, pero juntos generan dos caminos distintos para "vender" (uno completo, uno fantasma) y obligan a pedir datos que, en la mayoría de las ventas reales de este negocio, nadie va a querer dar. Esta feature no agrega funcionalidad nueva: ajusta la integración entre features ya existentes para que el flujo cotidiano de venta sea consistente de punta a punta.

## Criterios de aceptación

- [x] El botón "-Salida" en `producto_list.html` ya no llama a `movimiento_crear`. En su lugar, lleva a "Nueva Venta" (`pedido_crear`) con el producto correspondiente ya agregado como primer ítem del formulario.
- [x] El botón "+Entrada" se mantiene apuntando a `movimiento_crear`, pero se relabelea para dejar en claro que es una corrección manual de stock, no una compra a proveedor (que debe pasar por Órdenes de Compra).
- [x] En el formulario de "Nueva Venta" (`pedido_form.html`) existe un link "+ Nuevo Cliente" que abre la vista de alta y listado `cliente_list_crear` (URL `cliente_list`) en una pestaña nueva.
- [x] `Pedido.cliente` pasa a ser opcional (`null=True, blank=True`).
- [x] `PedidoForm` incluye un campo de texto libre y opcional ("Nombre del comprador") para cuando no se selecciona un cliente registrado.
- [x] `crear_pedido` acepta `cliente_id=None`. En ese caso: `pedido.cliente` queda `null`; `cliente_nombre` se completa con el texto libre ingresado o, si no se ingresó nada, con `"Consumidor Final"`; `cliente_tipo_documento`, `cliente_numero_documento` y `cliente_telefono` quedan vacíos.
- [x] Ningún template, vista ni representación de `Pedido` dereferencia `pedido.cliente.<campo>` para mostrar datos del comprador: `pedido_list.html`, `pedido_confirm_cancel.html` y `Pedido.__str__` usan los campos de snapshot (`cliente_nombre`, etc.), con `"Consumidor Final"` como respaldo cuando corresponda.
- [x] Un pedido sin cliente registrado se puede visualizar, listar y cancelar con el mismo comportamiento que uno con cliente, sin excepciones ni casos especiales en esas vistas.
- [x] Los tests existentes de `Pedido`/`crear_pedido` con cliente real siguen pasando sin modificarse.
- [x] El botón "-Salida" pasa el producto por GET y `pedido_crear` lo precarga en la fila inicial del formset desde Django, sin parseo de query params en JavaScript.

## Fuera de alcance

- Renombrar la nomenclatura interna `Pedido`/`pedido_*` a `Venta`/`venta_*`. Se evaluó y se descarta: la mezcla actual (nombre técnico "Pedido", nombre comercial "Venta") es consistente dentro de cada capa y no genera confusión real; el costo de renombrar todo supera el beneficio.
- Reportes o estadísticas agregadas de ventas a "Consumidor Final" (quedan todas agrupadas bajo el mismo texto, sin desagregar). Se puede revisar en una feature futura si hace falta.
- Un botón "+ Nuevo Proveedor" equivalente en Órdenes de Compra (no se detectó como problema en esta revisión; se puede sumar después con el mismo patrón si hace falta).