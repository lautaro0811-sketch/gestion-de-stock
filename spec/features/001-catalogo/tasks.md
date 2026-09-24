# 001 · Catálogo y Modelos Base — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas; marca `[x]` al completarlas._

- [x] Configurar el entorno virtual, instalar Django e inicializar el proyecto `core` y la app `inventario`[cite: 2].
- [x] Registrar la app en `settings.py` y configurar idioma (`es-ar`) y zona horaria[cite: 2].
- [x] Definir los modelos `Categoria`, `Producto` y `Movimiento` en `inventario/models.py`[cite: 2].
- [x] Crear y aplicar las migraciones a la base de datos SQLite[cite: 2].
- [x] Configurar `inventario/admin.py` para visualizar modelos, marcando `stock_actual` como campo de solo lectura[cite: 2].
- [x] Crear `CategoriaForm` y `ProductoForm` en `inventario/forms.py`, excluyendo explícitamente `stock_actual` para proteger la regla de negocio[cite: 2].
- [x] Implementar las vistas CRUD en `inventario/views.py` (`producto_list`, `producto_crear`, `producto_editar`, `producto_desactivar`, `categoria_list_crear`)[cite: 2].
- [x] Crear el archivo de rutas `inventario/urls.py` y conectarlo con las URLs globales en `core/urls.py`[cite: 2].
- [x] Desarrollar la estructura base `templates/base.html` con variables CSS, alertas y navegación[cite: 2].
- [x] Construir las plantillas HTML para listar, crear/editar y dar de baja lógica a los productos y categorías[cite: 2].
- [x] Probar la navegación, validar la protección del campo de stock y comprobar el filtro de stock crítico desde el navegador[cite: 2].
- [x] Validar contra los criterios de aceptación de `spec.md`.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.