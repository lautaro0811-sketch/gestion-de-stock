# 013 · Orden de Compra en PDF — Tareas

- [x] Crear la plantilla aislada `templates/inventario/pdf/orden_compra.html` estructurada en formato A4 con CSS interno.
- [x] Crear la vista `orden_compra_pdf_view` en `inventario/views.py` utilizando `xhtml2pdf.pisa`.
- [x] Agregar la ruta correspondiente en `inventario/urls.py`.
- [x] Modificar `templates/inventario/orden_compra_detalle.html` para incluir el botón "Descargar PDF" en la botonera de acciones.
- [x] Escribir un test en `inventario/tests.py` que valide que el endpoint de descarga de la OC devuelve un código 200 y el `content-type` correcto (`application/pdf`).
- [x] Validar contra los criterios de aceptación de `spec.md`.
- [ ] Mover la feature a "Hecho" en `../../constitution/roadmap.md`[cite: 9].