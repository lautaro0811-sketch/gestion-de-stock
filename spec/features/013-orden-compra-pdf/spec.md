# 013 · Orden de Compra en PDF

**Estado:** implementado ✅

## Qué hace
Permite al usuario generar y descargar un documento PDF estructurado como una "Orden de Compra" formal a partir de un registro de compra existente. El documento está diseñado en formato A4 e incluye los datos del proveedor, los detalles de los productos solicitados y los costos pactados.

## Por qué
Formaliza el pedido de mercadería de cara a los proveedores externos. Permite tener un respaldo físico o digital inalterable de las cantidades y precios unitarios de compra pactados antes de que la mercadería ingrese al sistema.

## Criterios de aceptación
- [x] En la vista de detalle de una Orden de Compra, existe un botón "Descargar PDF" en la botonera de acciones.
- [x] Al hacer clic, el sistema genera un archivo `.pdf` descargable con la nomenclatura `OC-YYYY-XXXX.pdf` (utilizando el número de operación).
- [x] El documento PDF tiene formato A4 e incluye una cabecera con el título "ORDEN DE COMPRA", el Número de Operación, la Fecha y el Estado actual.
- [x] El documento incluye los datos del Proveedor (Razón Social, DNI/CUIT, Teléfono, Correo).
- [x] El documento muestra una tabla con los ítems (Cantidad, Producto, Precio Unitario de Compra y Subtotal) y el Total al pie.
- [x] La generación técnica reutiliza la librería `xhtml2pdf` instalada previamente, sin requerir nuevas dependencias de sistema operativo.

## Fuera de alcance
- Envío automatizado del PDF por correo electrónico al proveedor (la descarga y el envío se hacen manualmente).