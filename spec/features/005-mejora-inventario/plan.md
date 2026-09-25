# Plan de implementación – 005‑mejora‑inventario

### 1️⃣ Exportar CSV
- Crear una nueva vista `inventario/export_csv` (función basada en la vista de listado existente).
- Leer los mismos filtros que la vista de listado (`q`, `categoria`, `stock_bajo`) y aplicarlos al queryset.
- Generar el CSV con `csv.writer`, incluir encabezados y respetar orden de columnas definido por `?orden` y `dir` (re‑usar la lógica de ordenamiento).
- Devolver `HttpResponse` con `Content‑Disposition: attachment; filename="inventario.csv"`.

### 2️⃣ Accesos rápidos (+Entrada / -Salida)
- Editar el template `inventario/producto_list.html`:
  * Añadir dos botones en cada fila (`<a>` con clases `.btn-entrada` y `.btn-salida`).
  * Cada botón construye la URL a `movimiento_crear` con los parámetros `producto=<id>` y `tipo=ENTRADA` / `tipo=SALIDA`.
- No tocar la lógica del view `movimiento_crear`; solo se provee la URL correcta.

### 2.1️⃣ Modificar `movimiento_crear` para usar los parámetros GET `producto` y `tipo`
- En `inventario/views.py`, leer `producto` y `tipo` de `request.GET`.
- Construir `initial_data = {}`; si `producto` está presente, intentar convertirlo a `int` con `try/except`; si falla, simplemente no añadirlo.
- Si `tipo` está presente, asignarlo también a `initial_data`.
- Instanciar el formulario con `MovimientoUnificadoForm(initial=initial_data)`.
- No cambiar la lógica de negocio del `POST`.

### 3️⃣ Ordenamiento de columnas
- Modificar la vista `producto_list` (en `inventario/views.py`) para leer `orden` y `dir` de la query‑string.
- Validar `orden` contra whitelist `['nombre', 'categoria', 'stock_actual', 'stock_minimo']`.
- Aplicar `order_by` al queryset (`campo` o `-campo` según `dir`).
- En el template `producto_list.html`:
  * Añadir enlaces en los encabezados de tabla que incluyan los parámetros actuales y alternen la dirección.
  * Mostrar una flecha (`↑` / `↓`) junto a la columna ordenada y aplicar la clase CSS `.active-sort`.

### 4️⃣ Migración de estilos en línea (para cumplir con la tarea pendiente de 003‑dashboard)
- Buscar en todos los templates bajo `templates/` los atributos `style="..."`.
- Reemplazarlos por clases definidas en `static/css/style.css`.
- Actualizar `static/css/style.css` con los nuevos selectores (ejemplo: `.badge-alert`, `.table-compact`, etc.).
