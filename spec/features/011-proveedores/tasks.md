# 011 · Proveedores — Tareas

- [ ] Confirmar contra el código real la implementación actual de la validación de documento en Cliente antes de extraerla.
- [ ] Crear inventario/validators.py con validar_documento(tipo_documento, numero_documento).
- [ ] Refactorizar Cliente.clean() y ClienteForm.clean() para usar validar_documento(...), conservando la limpieza del documento/teléfono y los casos opcionales actuales de Cliente.
- [ ] Correr los tests existentes de Cliente y confirmar que todos siguen pasando tras el refactor.
- [ ] Crear el modelo Proveedor con sus campos y baja lógica.
- [ ] Generar y aplicar la migración.
- [ ] Crear ProveedorForm.
- [ ] Implementar proveedor_list_crear con búsqueda (documento, nombre, ID) y paginación.
- [ ] Implementar proveedor_desactivar.
- [ ] Agregar las rutas en inventario/urls.py.
- [ ] Crear el template proveedor_list.html, sin estilos en línea.
- [ ] Crear el template proveedor_confirm_delete.html para confirmar la baja por GET, siguiendo el flujo de cliente_desactivar.
- [ ] Agregar el link "Proveedores" en el sidebar de base.html.
- [ ] Registrar Proveedor en inventario/admin.py.
- [ ] Escribir tests: alta válida; rechazo de documento duplicado; validación de DNI/CUIT (reutilizando los mismos casos de prueba que Cliente); búsqueda por documento, nombre parcial e ID; baja lógica no borra el registro; listado solo muestra activos.
- [ ] Correr python manage.py test (suite completa) y confirmar que todo pasa, Cliente incluido.
- [ ] Validar contra los criterios de aceptación de spec.md.
- [ ] Mover la feature a "Hecho" en ../../constitution/roadmap.md.