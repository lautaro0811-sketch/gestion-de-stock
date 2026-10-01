# 007 · Clientes

**Estado:** implementado

## Qué hace

Incorpora un registro de clientes al sistema. Cada cliente tiene nombre, DNI, correo y teléfono, y queda identificado por un número de cliente (su ID). Se agrega una vista nueva en el dashboard, accesible desde el menú lateral, donde se puede dar de alta un cliente y buscar entre los existentes por DNI, nombre o número de cliente.

## Por qué

Es la base para poder asociar las ventas (salidas de stock) a una persona concreta, algo que hoy no existe en el sistema. Sin un registro de clientes, no se puede saber quién compró qué, ni emitir comprobantes a nombre de alguien. Este feature no incluye las ventas en sí (eso es 008-pedidos-venta); solo deja listo el padrón de clientes sobre el que esa feature se va a apoyar.

## Criterios de aceptación

- [x] Existe un modelo `Cliente` con los campos: `nombre`, `dni` (único), `correo` (opcional), `telefono` (opcional) y `activo` (booleano, por defecto `True`).
- [x] El sistema impide registrar dos clientes con el mismo DNI, mostrando un error claro en el formulario.
- [x] Hay una vista "Clientes" accesible desde el menú lateral del dashboard.
- [x] Esa vista permite dar de alta un cliente nuevo con un formulario simple (nombre, DNI, correo, teléfono).
- [x] El listado muestra únicamente los clientes activos, con su número de cliente (ID), nombre, DNI, correo y teléfono.
- [x] Existe un buscador que filtra el listado por DNI, por nombre (coincidencia parcial) o por número de cliente (ID exacto).
- [x] Existe una acción de baja lógica (desactivar cliente) análoga a la de `Producto`, que cambia `activo` a `False` sin borrar el registro de la base de datos.
- [x] El listado está paginado, siguiendo el mismo criterio ya usado en `producto_list`.


## Fuera de alcance

- Asociar clientes a ventas o pedidos. Se implementa en `008-pedidos-venta`.
- Mostrar el historial de compras de cada cliente. Depende de que exista `Pedido` (008); se agrega ahí o en una revisión posterior de esta vista.
- Edición de los datos de un cliente ya cargado (por ahora solo alta y baja lógica).
- Validación de formato de DNI, correo o teléfono más allá de los validadores básicos de Django (unicidad del DNI y formato de email estándar).
- Roles, permisos o restricciones de acceso a la vista de clientes.