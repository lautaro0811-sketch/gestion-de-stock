# 009 · Generación de Pedido en PDF (Remito) — Tareas

- [x] Crear el archivo `templates/inventario/pdf/remito.html` con estructura de comprobante clásico, placeholders para la empresa y estilos CSS integrados (`<style>`).
- [x] Modificar `inventario/views.py`: importar `render_to_string` y crear la vista `pedido_pdf_view`.
- [x] Implementar la lógica en la vista para recopilar el pedido, renderizar el string HTML e invocar la skill PDF del agente.
- [x] Configurar la vista para que retorne el archivo como descarga (`attachment; filename=Remito_YYYY-XXXX.pdf`).
- [x] Modificar `inventario/urls.py` agregando la ruta `path('pedidos/<int:pk>/pdf/', views.pedido_pdf_view, name='pedido_pdf')`.
- [x] Modificar `templates/inventario/pedido_detalle.html` para incluir el botón de descarga en la cabecera.
- [x] Probar la generación del PDF con un pedido real y verificar que la tabla de ítems y los precios históricos se visualicen correctamente.
- [x] Validar contra los criterios de aceptación de `spec.md`.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.