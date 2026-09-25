# 005 · Mejora Inventario

**Estado:** pendiente ⏳

## Qué hace

Añade a la vista de Inventario tres mejoras de usabilidad y exportación:

1. **Exportar CSV** del listado de productos, respetando cualquier filtro activo (búsqueda libre, filtro por categoría y opción “solo alertas”).
2. **Botones de acceso rápido** “+Entrada” y “‑Salida” en cada fila de la tabla que redirigen a la vista existente `movimiento_crear` con los parámetros `producto` (id) y `tipo` (`ENTRADA` o `SALIDA`) pre‑seleccionados. No se introduce lógica de negocio nueva; solo la generación de la URL.
3. **Ordenamiento de columnas** mediante query‑params `?orden=campo&dir=asc|desc`. Sólo se permiten los campos:
   - `nombre`
   - `categoria`
   - `stock_actual`
   - `stock_minimo`  
   La columna activa muestra una flecha indicadora de dirección y un estilo visual que la resalta.

## Criterios de aceptación

- Se genera un archivo CSV válido (UTF‑8, separador coma) cuyo contenido refleja exactamente los productos mostrados en la tabla tras aplicar los filtros.
- Los botones **+Entrada** y **‑Salida** llevan a `movimiento_crear` con URL del tipo:
  ```
  /movimiento_crear?producto=<ID_DEL_PRODUCTO>&tipo=ENTRADA
  ```
  y
  ```
  /movimiento_crear?producto=<ID_DEL_PRODUCTO>&tipo=SALIDA
  ```
  respectivamente.
- Cambiar los parámetros `orden` y `dir` en la URL **recarga la página** (no hay recarga “ajax”, la petición completa vuelve a renderizarse) y muestra la flecha de dirección correcta; sólo los campos listados en la whitelist son aceptados.
- Si se envía un valor de `orden` que no esté en la whitelist, la vista ignora el parámetro y mantiene el orden por defecto, sin lanzar excepción.
- Los estilos de los nuevos botones y de la flecha de ordenamiento utilizan clases definidas en `static/css/style.css`; no aparecen atributos `style="..."` en los templates.

## Fuera de alcance

- No se introduce ningún nuevo modelo o campo en la base de datos; la exportación CSV y el ordenamiento trabajan exclusivamente con el queryset existente.
- No se añaden frameworks CSS o JS externos (Bootstrap, Tailwind, etc.). Todo el estilo se mantiene en `static/css/style.css`.
- No se implementa lógica de negocio para crear movimientos; la vista `movimiento_crear` sigue manejando la creación como antes.
- La gestión de permisos y autenticación permanece sin cambios.
