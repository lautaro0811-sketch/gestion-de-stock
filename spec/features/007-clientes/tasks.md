# 007 · Clientes — Tareas

- [x] Confirmar con el código real la convención de vistas/templates a reutilizar (`categoria_list_crear` como referencia) antes de escribir nada.
- [x] Crear el modelo `Cliente` en `inventario/models.py` con sus campos y la baja lógica.
- [x] Generar y aplicar la migración.
- [x] Crear `ClienteForm` en `inventario/forms.py`.
- [x] Implementar `cliente_list_crear` con búsqueda (DNI, nombre, ID) y paginación.
- [x] Implementar `cliente_desactivar` (baja lógica).
- [x] Agregar las rutas en `inventario/urls.py`.
- [x] Crear el template `cliente_list.html`, siguiendo la identidad visual existente (sin estilos en línea).
- [x] Agregar el link "Clientes" en el sidebar de `base.html`.
- [x] Registrar `Cliente` en `inventario/admin.py`.
- [x] Escribir tests: alta de cliente válido; rechazo de DNI duplicado; búsqueda por DNI, por nombre parcial y por ID; baja lógica no borra el registro; el listado solo muestra clientes activos.
- [x] Correr `python manage.py test` y confirmar que todo pasa.
- [x] Validar contra los criterios de aceptación de `spec.md`.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.


## Mantenimiento (checklist recurrente)

_No aplica por ahora. Se revisará si 008-pedidos-venta requiere ajustes en este modelo (por ejemplo, un campo adicional) una vez que se implemente esa feature._