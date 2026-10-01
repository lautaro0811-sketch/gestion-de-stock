# 007 · Clientes

**Estado:** implementado

## Qué hace

Incorpora un registro de clientes al sistema. Cada cliente tiene nombre / razón social, tipo de documento (DNI o CUIT), número de documento (único), domicilio de entrega (opcional), correo y teléfono (opcional), y queda identificado por un número de cliente (su ID). Se agrega una vista nueva en el dashboard, accesible desde el menú lateral, donde se puede dar de alta un cliente y buscar entre los existentes por documento (CUIT / DNI), nombre o número de cliente.

## Por qué

Es la base para poder asociar las ventas (salidas de stock) a una persona o empresa concreta, algo que hoy no existe en el sistema. Sin un registro de clientes, no se puede saber quién compró qué, ni emitir comprobantes a nombre de alguien. Este feature no incluye las ventas en sí (eso es 008-pedidos-venta); solo deja listo el padrón de clientes sobre el que esa feature se va a apoyar.

## Criterios de aceptación

- [x] Existe un modelo `Cliente` con los campos:
  - `nombre`: CharField, "Nombre / Razón social" (requerido).
  - `tipo_documento`: CharField con choices `[("DNI", "DNI"), ("CUIT", "CUIT")]`, "Tipo de documento" (requerido en form).
  - `numero_documento`: CharField, único, "CUIT / DNI" (requerido en form).
  - `domicilio`: CharField, "Domicilio de entrega" (opcional).
  - `correo`: EmailField, "Correo electrónico" (opcional).
  - `telefono`: CharField, "Teléfono" (opcional, validado a mínimo 6 dígitos si se ingresa).
  - `activo`: BooleanField, por defecto `True`.
  - `fecha_creacion`: DateTimeField, `auto_now_add=True`.
- [x] Validación según `tipo_documento`:
  - Si `tipo_documento` es `DNI`: `numero_documento` normalizado (solo dígitos) debe tener 7 u 8 dígitos.
  - Si `tipo_documento` es `CUIT`: `numero_documento` normalizado debe tener 11 dígitos y validar el algoritmo oficial de dígito verificador módulo 11 (con factores 5, 4, 3, 2, 7, 6, 5, 4, 3, 2).
- [x] Validación de `telefono`: mínimo 6 dígitos tras normalizar si no está vacío.
- [x] Normalización automática de `numero_documento` y `telefono` a solo dígitos antes de guardar.
- [x] El sistema impide registrar dos clientes con el mismo `numero_documento` (incluso si se ingresan con distintos formatos de puntos o guiones).
- [x] Hay una vista "Clientes" accesible desde el menú lateral del dashboard.
- [x] Esa vista permite dar de alta un cliente nuevo con `ClienteForm` con etiquetas actualizadas:
  - `nombre` → "Nombre / Razón social"
  - `tipo_documento` → "Tipo de documento"
  - `numero_documento` → "CUIT / DNI"
  - `domicilio` → "Domicilio de entrega"
- [x] El listado muestra únicamente los clientes activos, con su número de cliente (ID), Nombre / Razón social, Documento (`tipo_documento` + `numero_documento`), Domicilio de entrega, Correo y Teléfono.
- [x] Existe un buscador que filtra el listado por `numero_documento`, por `nombre` (coincidencia parcial) o por número de cliente (`id` exacto).
- [x] Existe una acción de baja lógica (desactivar cliente) análoga a la de `Producto`, que cambia `activo` a `False` sin borrar el registro de la base de datos.
- [x] El listado está paginado, siguiendo el mismo criterio ya usado en `producto_list`.

## Fuera de alcance

- Asociar clientes a ventas o pedidos. Se implementa en `008-pedidos-venta`.
- Mostrar el historial de compras de cada cliente. Depende de que exista `Pedido` (008); se agrega ahí o en una revisión posterior de esta vista.
- Edición de los datos de un cliente ya cargado (por ahora solo alta y baja lógica).
- Roles, permisos o restricciones de acceso a la vista de clientes.