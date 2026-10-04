# 011 · Proveedores

**Estado:** propuesta

## Qué hace

Incorpora un registro de proveedores, simétrico al de clientes (007). Cada proveedor tiene nombre o razón social, tipo y número de documento (DNI o CUIT, con la misma validación ya usada para clientes), domicilio, correo y teléfono. Se agrega una vista "Proveedores" en el dashboard con alta y búsqueda por documento, nombre o número de proveedor (ID).

## Por qué

Es la base para poder registrar órdenes de compra (012): antes de poder comprarle mercadería a alguien, el sistema necesita saber quién es ese alguien. Mantiene el mismo patrón ya validado con clientes para no introducir una forma distinta de modelar el mismo tipo de entidad.

## Criterios de aceptación

- [ ] Existe un modelo `Proveedor` con los campos: `nombre` (razón social), `tipo_documento` (DNI/CUIT), `numero_documento` (único), `domicilio` (opcional), `correo` (opcional), `telefono` (opcional) y `activo` (booleano, por defecto `True`).
- [ ] La validación de `tipo_documento`/`numero_documento` reutiliza la misma lógica ya implementada para `Cliente`, extraída a una función o validador compartido: DNI de 7 u 8 dígitos y CUIT de 11 dígitos, sin verificar el dígito verificador.
- [ ] El sistema impide registrar dos proveedores con el mismo número de documento.
- [ ] Hay una vista "Proveedores" accesible desde el menú lateral del dashboard, con alta (formulario) y listado paginado de proveedores activos.
- [ ] Existe un buscador que filtra por número de documento, por nombre (coincidencia parcial) o por número de proveedor (ID exacto).
- [ ] Existe una acción de baja lógica (desactivar proveedor), que cambia `activo` a `False` sin borrar el registro.
- [ ] Los tests existentes de `Cliente` (incluyendo validación de documento) siguen pasando después de extraer la lógica compartida.

## Fuera de alcance

- Órdenes de compra y su vínculo con proveedores. Se implementa en `012-ordenes-compra`.
- Generación de PDF de la orden de compra. Se implementa en `013-orden-compra-pdf`.
- Reflejar compras como egresos en Caja. Se implementa en `014-caja-egresos-proveedores`.
- Edición de los datos de un proveedor ya cargado (por ahora solo alta y baja lógica, igual que en clientes).
- Historial de compras por proveedor en esta misma vista (depende de que exista `OrdenCompra`, se evalúa en 012 o en una revisión posterior).