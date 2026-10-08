# 015 · Integración del Flujo Operativo — Tareas

- [x] Auditar accesos directos: encontrados en pedido_list.html, pedido_confirm_cancel.html y Pedido.__str__; caja_dashboard.html solo muestra el número de operación. Sustituirlos por snapshots/fallback antes de permitir cliente nulo.
- [x] Revisar "+ Nuevo Producto": el formulario de Órdenes de Compra abre un diálogo AJAX; para cliente se usa el enlace a la vista cliente_list_crear (URL cliente_list) en pestaña nueva solicitado por el criterio de aceptación.
- [x] Revisar el formset Vanilla JS: su fila extra inicial se renderiza desde Django y se enlaza al cargar; la vista puede precargar producto en initial sin agregar parsing de GET en JS.
- [x] Cambiar Pedido.cliente a null=True, blank=True.
- [x] Generar y aplicar la migración.
- [x] Modificar PedidoForm: cliente opcional, nuevo campo nombre_comprador.
- [x] Modificar crear_pedido para aceptar cliente_id=None y nombre_comprador, completando el snapshot con "Consumidor Final" por defecto.
- [x] Ajustar pedido_crear (views.py) para pasar estos valores al servicio.
- [x] Cambiar el botón "-Salida" en producto_list.html para redirigir a pedido_crear con el producto activo precargado por Django en la fila inicial del formset.
- [x] Relabelear/aclarar el botón "+Entrada" sin cambiar su funcionalidad.
- [x] Agregar el link "+ Nuevo Cliente" en pedido_form.html.
- [x] Agregar las notas de extensión en 005/spec.md y en los archivos existentes 007/spect.md, 008/spect.md y 009/spect.md (no crear ni renombrar archivos de documentación).
- [x] Tests: pedido sin cliente queda en null con snapshot "Consumidor Final"; el nombre libre se guarda; detalle y remito muestran el snapshot; pedido_list muestra pedidos mixtos; la cancelación devuelve stock; "-Salida" arma la URL y el producto queda precargado; "+ Nuevo Cliente" está presente; las pruebas existentes con cliente registrado siguen pasando.
- [x] Correr python manage.py test (suite completa) y confirmar que todo pasa: 106 tests OK.
- [x] Validar contra los criterios de aceptación de spec.md.
- [x] Mover la feature a "Hecho" en ../../constitution/roadmap.md.