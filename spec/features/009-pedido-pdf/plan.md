# 009 · Generación de Pedido en PDF (Remito) — Plan

## Enfoque

Nos apoyaremos en la **skill pdf** del agente para abstraer la complejidad técnica de generar archivos binarios. Crearemos una vista en Django que recopile la información del `Pedido`, renderice un template HTML diseñado específicamente para impresión (con CSS básico integrado y sin elementos de navegación) y pase ese HTML a la skill para su conversión a PDF.

## Implementación

1. **Plantilla de Impresión (`templates/inventario/pdf/remito.html`)**: 
   - Crear un HTML semántico y aislado.
   - *Bloque Superior*: Textos estáticos tipo `[Nombre de tu Empresa]` y `[Tus datos de contacto]` como placeholders temporales. Recuadro con el Número de Operación y Fecha.
   - *Bloque Cliente*: Nombre, DNI.
   - *Bloque Detalle*: Tabla con Cantidad, Producto, Precio Unit., Subtotal y Total final.
   - Incluir todo el CSS en una etiqueta `<style>` interna para garantizar que el motor PDF lo interprete correctamente.
2. **Controlador (`inventario/views.py`)**: 
   - Crear la vista `pedido_pdf_view(request, pk)`.
   - Utilizar `get_object_or_404(Pedido.objects.prefetch_related('items__producto', 'cliente'), pk=pk)` para optimizar consultas de base de datos.
   - Renderizar el HTML en memoria usando `render_to_string('inventario/pdf/remito.html', context)`.
   - Invocar la skill PDF para transformar el string HTML en un archivo binario.
   - Retornar un `HttpResponse` con `content_type='application/pdf'` y el header `Content-Disposition: attachment; filename="Remito_...pdf"`.
3. **Ruteo (`inventario/urls.py`)**: 
   - Conectar la vista bajo la ruta `pedidos/<int:pk>/pdf/`.
4. **Interfaz (`templates/inventario/pedido_detalle.html`)**: 
   - Agregar el botón "Descargar Remito PDF" en la botonera de acciones del pedido.

## Decisiones

- **Datos de la empresa hardcodeados/genéricos** — Se decidió no modelar aún la entidad "Empresa" en la base de datos para no desviar el foco operativo del sistema. Se usarán placeholders estáticos.
- **Plantilla HTML exclusiva y aislada** — No se reutiliza la vista `pedido_detalle.html` porque los motores de conversión a PDF requieren estructuras más rígidas (tablas, anchos fijos) y fallan al procesar layouts complejos o sidebars.
- **Delegación a la Skill PDF** — Mantiene el entorno Python liviano y multiplataforma sin requerir la instalación de librerías nativas de sistema operativo.

## Riesgos

- **Manejo de codificación (Encoding)** — Los motores PDF pueden tener problemas con caracteres especiales (ñ, acentos, el símbolo $). 
  - *Mitigación*: Forzar explícitamente `<meta charset="UTF-8">` en el `<head>` del template `remito.html`.