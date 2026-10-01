# 007 · Clientes — Tareas

- [ ] Confirmar con el código real la convención de vistas/templates a reutilizar (`categoria_list_crear` como referencia) antes de escribir nada.
- [ ] Crear el modelo `Cliente` en `inventario/models.py` con sus campos y la baja lógica.
- [ ] Generar y aplicar la migración.
- [ ] Crear `ClienteForm` en `inventario/forms.py`.
- [ ] Implementar `cliente_list_crear` con búsqueda (DNI, nombre, ID) y paginación.
- [ ] Implementar `cliente_desactivar` (baja lógica).
- [ ] Agregar las rutas en `inventario/urls.py`.
- [ ] Crear el template `cliente_list.html`, siguiendo la identidad visual existente (sin estilos en línea).
- [ ] Agregar el link "Clientes" en el sidebar de `base.html`.
- [ ] Registrar `Cliente` en `inventario/admin.py`.
- [ ] Escribir tests: alta de cliente válido; rechazo de DNI duplicado; búsqueda por DNI, por nombre parcial y por ID; baja lógica no borra el registro; el listado solo muestra clientes activos.
- [ ] Correr `python manage.py test` y confirmar que todo pasa.
- [ ] Validar contra los criterios de aceptación de `spec.md`.
- [ ] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.

## Mantenimiento (checklist recurrente)

_No aplica por ahora. Se revisará si 008-pedidos-venta requiere ajustes en este modelo (por ejemplo, un campo adicional) una vez que se implemente esa feature._