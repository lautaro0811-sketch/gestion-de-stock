# 011 · Proveedores — Tareas

- [x] Confirmar contra el código real la implementación actual de la validación de documento en Cliente antes de extraerla.
- [x] Crear inventario/validators.py con validar_documento(tipo_documento, numero_documento).
- [x] Refactorizar Cliente.clean() y ClienteForm.clean() para usar validar_documento(...), conservando la limpieza del documento/teléfono y los casos opcionales actuales de Cliente.
- [x] Correr los tests existentes de Cliente y confirmar que todos siguen pasando tras el refactor.
- [x] Crear el modelo Proveedor con sus campos y baja lógica.
- [x] Generar y aplicar la migración.
- [x] Crear ProveedorForm.
- [x] Implementar proveedor_list_crear con búsqueda (documento, nombre, ID) y paginación.
- [x] Implementar proveedor_desactivar.
- [x] Agregar las rutas en inventario/urls.py.
- [x] Crear el template proveedor_list.html, sin estilos en línea.
- [x] Crear el template proveedor_confirm_delete.html para confirmar la baja por GET, siguiendo el flujo de cliente_desactivar.
- [x] Agregar el link "Proveedores" en el sidebar de base.html.
- [x] Registrar Proveedor en inventario/admin.py.
- [x] Escribir tests: alta válida; rechazo de documento duplicado; validación de DNI/CUIT (reutilizando los mismos casos de prueba que Cliente); búsqueda por documento, nombre parcial e ID; baja lógica no borra el registro; listado solo muestra activos.
- [x] Correr python manage.py test (suite completa) y confirmar que todo pasa, Cliente incluido.
- [x] Validar contra los criterios de aceptación de spec.md.
- [x] Mover la feature a "Hecho" en ../../constitution/roadmap.md.