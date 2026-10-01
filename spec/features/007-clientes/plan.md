# 007 · Clientes — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Se modela `Cliente` como una entidad más dentro de la app `inventario`, siguiendo el mismo patrón ya usado para `Categoria` y `Producto`: modelo simple, baja lógica, vista basada en función, template propio sin frameworks externos. No se crea una app nueva (`clientes/`) para no fragmentar un proyecto chico sin necesidad, en línea con la convención de `tech-stack.md` de evitar complejidad innecesaria.

**Pendiente de confirmar antes de codear:** verificar contra `inventario/views.py` y `inventario/models.py` que esta decisión sigue teniendo sentido con la estructura actual, y relevar la convención real de nombres de vistas/templates (tomar `categoria_list_crear` y `categoria_list.html` como referencia más cercana, ya que combinan listado + alta en una sola vista).

## Implementación

1. **Modelo — `inventario/models.py`**: crear `Cliente` con `nombre` (CharField), `dni` (CharField, `unique=True`), `correo` (EmailField, `blank=True`), `telefono` (CharField, `blank=True`), `activo` (BooleanField, default `True`), `fecha_creacion` (DateTimeField, auto_now_add).
2. **Migración**: generar y aplicar la migración correspondiente.
3. **Formulario — `inventario/forms.py`**: crear `ClienteForm` (ModelForm) con los campos editables. La unicidad del DNI se valida vía el `unique=True` del modelo, que Django ya refleja como error de formulario.
4. **Vistas — `inventario/views.py`**:
   - `cliente_list_crear`: combina listado (con búsqueda y paginación) y alta, siguiendo el patrón de `categoria_list_crear`.
   - `cliente_desactivar`: baja lógica, análoga a `producto_desactivar`.
5. **Búsqueda**: en `cliente_list_crear`, leer `?q=` y filtrar con `Q(nombre__icontains=q) | Q(dni__icontains=q)`, más un filtro adicional por `id` exacto si `q` es numérico.
6. **URLs — `inventario/urls.py`**: agregar las rutas para las dos vistas nuevas.
7. **Templates — `templates/inventario/`**: crear `cliente_list.html` reutilizando la estructura visual de `categoria_list.html` (tarjeta de alta + tabla de listado), y un template de confirmación para la baja si hace falta uno nuevo (o reutilizar el patrón de `producto_confirm_delete.html`).
8. **Navegación — `templates/base.html`**: agregar el link "Clientes" en el sidebar, con su estado activo correspondiente.
9. **Admin — `inventario/admin.py`**: registrar `Cliente` para poder inspeccionarlo rápido durante el desarrollo.

## Decisiones

- **Un solo modelo, sin app nueva** — Mantener todo en `inventario` evita duplicar configuración (templates, estáticos, settings) para un proyecto de este tamaño. Se descartó crear una app `clientes` por ahora; si el sistema crece mucho, se puede migrar después.
- **DNI como identificador de unicidad, no como clave primaria** — Se seguirá usando el `id` autonumérico de Django como PK y "número de cliente" visible. Se descartó usar el DNI como PK para no atarse a un dato que en teoría podría necesitar corrección.
- **Reutilizar el patrón de `categoria_list_crear`** — Como es la vista más parecida (listado + alta en una sola pantalla), se usa como base en vez de replicar el patrón más complejo de `Producto` (que separa alta y edición en vistas distintas), ya que este feature no incluye edición.

## Riesgos

- **DNI con formatos distintos (con o sin puntos/guiones)** — Si no se normaliza, dos entradas del "mismo" DNI escrito distinto pasarían la validación de unicidad. Mitigación: normalizar el DNI (quitar separadores) antes de guardar, documentado como parte de la limpieza del formulario.
- **Búsqueda por ID ambigua con DNIs numéricos largos** — Si el buscador prioriza mal la coincidencia por ID vs. DNI, podría confundir resultados. Mitigación: tratar el ID como filtro exacto únicamente cuando el texto ingresado coincide con el total de dígitos esperados para un ID, o simplemente mostrar como resultados la unión de todos los filtros aplicables sin necesidad de distinguir cuál matcheó.