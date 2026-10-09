# 016 · Filtros en Caja — Tareas

- [ ] Revisar cómo quedó resuelta la construcción de query params sin duplicar orden/dir en producto_list.html (005), para reutilizar el mismo mecanismo.
- [ ] Modificar caja_dashboard (views.py): leer y validar periodo, mes, anio, tipo.
- [ ] Calcular total_ingresos, total_egresos, saldo a partir del queryset filtrado solo por período.
- [ ] Calcular la tabla de movimientos a partir de período + tipo combinados.
- [ ] Agregar mostrar_saldo_periodo al contexto.
- [ ] Agregar los botones de período (Todo / Este mes / Este año) en caja_dashboard.html.
- [ ] Agregar el selector de mes + año específico.
- [ ] Agregar el selector de tipo (Todos / Ingresos / Egresos), afectando solo la tabla.
- [ ] Condicionar el título de la tarjeta de saldo según mostrar_saldo_periodo.
- [ ] Tests: filtro "este mes" recalcula ingresos/egresos/saldo correctamente con movimientos de distintos meses; filtro "este año"; filtro de mes/año específico pasado; un mes sin movimientos muestra $0 sin error; filtro de tipo=INGRESO no cambia los totales de las tarjetas, solo oculta las filas de egreso en la tabla; parámetros inválidos (mes=13, anio="abc", tipo="XYZ") caen al valor por defecto sin romper la vista; los links de filtro no duplican query params al combinarse.
- [ ] Correr python manage.py test (suite completa) y confirmar que todo pasa.
- [ ] Validar contra los criterios de aceptación de spec.md.
- [ ] Mover la feature a "Hecho" en ../../constitution/roadmap.md.