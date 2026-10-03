# 009 · Generación de Pedido en PDF (Remito)

**Estado:** completado ✅

## Qué hace

Permite al usuario generar y descargar un documento PDF estructurado como un "remito" o comprobante a partir de un pedido de venta. El documento está orientado a impresión tipo ticket / comprobante operativo y incluye todos los datos esenciales de la operación para ser entregado al cliente, utilizando un membrete genérico para los datos de la empresa emisora.

## Por qué

Digitaliza la entrega de comprobantes y permite tener un respaldo físico o enviarlo al cliente. Un remito claro mejora la imagen del negocio y sirve como constancia de los artículos entregados y los precios congelados acordados en la operación.

## Criterios de aceptación

- [x] En la vista de detalle de un pedido (`pedido_detalle.html`), existe un botón destacado "Descargar PDF" o "Imprimir Remito".
- [x] Al hacer clic, el sistema genera un archivo `.pdf` descargable con la nomenclatura `Remito_YYYY-XXXX.pdf` (usando el número de operación).
- [x] El documento PDF incluye un espacio genérico/placeholder en la cabecera para los datos de la Empresa.
- [x] El documento PDF incluye los datos del Cliente: Nombre completo y DNI/contacto (si están registrados).
- [x] El documento PDF incluye los datos de la Operación: Número correlativo (`2026-0001`), Fecha de la venta y Estado.
- [x] El documento PDF muestra una tabla clara con los ítems: Producto, Cantidad, Precio Unitario (histórico congelado) y Subtotal.
- [x] El documento PDF muestra el Total de la operación al pie de la tabla.
- [x] La generación técnica del archivo se realiza con `xhtml2pdf`, sin depender de WeasyPrint ni ReportLab.

## Fuera de alcance

- Configuración dinámica de los datos de la empresa (logo, razón social, CUIT). Queda diferido para una feature futura de "Configuración del Sistema"; por ahora se usan textos estáticos o placeholders.
- Envío automatizado de correos electrónicos con el PDF adjunto.