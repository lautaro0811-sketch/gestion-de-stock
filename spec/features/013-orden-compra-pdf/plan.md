# 013 · Orden de Compra en PDF — Plan

## Enfoque
Replicaremos el patrón arquitectónico de la Feature 009 (Remito PDF). Crearemos una vista en Django que recopile la `OrdenCompra` y sus ítems, renderice una plantilla HTML aislada diseñada para impresión y utilice `xhtml2pdf` para retornar el binario directamente al navegador.

## Implementación
1. **Plantilla de Impresión (`templates/inventario/pdf/orden_compra.html`)**:
   - Crear un HTML semántico y aislado (no extiende de `base.html`).
   - Se utilizará formato A4 (estándar B2B) en lugar del formato ticket térmico de 80mm usado en las ventas.
   - Incluir todo el CSS en una etiqueta `<style>` interna para garantizar su correcta interpretación por el motor de `xhtml2pdf` (excepción justificada a la regla de estilos externos)[cite: 11].
2. **Controlador (`inventario/views.py`)**:
   - Crear la vista `orden_compra_pdf_view(request, pk)`.
   - Utilizar `get_object_or_404(OrdenCompra.objects.prefetch_related('items__producto', 'proveedor'), pk=pk)` para optimizar la consulta.
   - Renderizar el HTML con `render_to_string` y convertirlo con `xhtml2pdf.pisa.CreatePDF`.
   - Retornar un `HttpResponse` con `content_type='application/pdf'` y `Content-Disposition: attachment; filename="OC-...pdf"`.
3. **Ruteo (`inventario/urls.py`)**:
   - Conectar la ruta `ordenes-compra/<int:pk>/pdf/`.
4. **Interfaz (`templates/inventario/orden_compra_detalle.html`)**:
   - Agregar el botón "Descargar PDF" (clase `.btn-secondary`) dentro del contenedor `.form-actions` u homólogo.

## Decisiones
- **Formato A4 B2B:** Mientras que los comprobantes de venta de mostrador son informales (ticket), las órdenes de compra para proveedores externos requieren un aspecto comercial tradicional.
- **Reutilización tecnológica:** Usar `xhtml2pdf` mantiene la coherencia del stack y evita inflar el entorno con librerías nativas conflictivas.