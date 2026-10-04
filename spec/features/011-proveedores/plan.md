# 011 · Proveedores — Plan

## Enfoque

Se modela `Proveedor` dentro de la app `inventario`, replicando la estructura de `Cliente` (modelo, formulario, vista combinada de listado+alta, baja lógica). La validación de tipo/número de documento se extrae a una función compartida que usan los modelos y formularios de ambas entidades. La validación actual solo comprueba longitud (no verifica el dígito verificador del CUIT); se conserva la normalización existente que quita caracteres no numéricos antes de validar.

## Implementación

1. **Validación compartida — `inventario/validators.py` (nuevo archivo)**: extraer la lógica de longitud de `Cliente.clean()` a `validar_documento(tipo_documento, numero_documento)`, incluyendo sus errores por campo y el caso de documento opcional de registros Cliente existentes.
2. **Refactor — `inventario/models.py` y `inventario/forms.py`**: hacer que `Cliente.clean()` y `ClienteForm.clean()` deleguen la comprobación de tipo/longitud a `validar_documento(...)`. Mantener fuera de esa función la limpieza de caracteres del número y las validaciones de teléfono. Confirmar que los tests existentes de `Cliente` siguen pasando sin cambios en su comportamiento.
3. **Modelo — `inventario/models.py`**: crear `Proveedor` con `nombre`, `tipo_documento`, `numero_documento` (unique=True), `domicilio` (blank=True), `correo` (EmailField, blank=True), `telefono` (blank=True), `activo` (default=True), `fecha_creacion` (auto_now_add). El `clean()` llama a la misma `validar_documento(...)`; a diferencia de Cliente, tipo y número son obligatorios para Proveedor.
4. **Migración**: generar y aplicar.
5. **Formulario — `inventario/forms.py`**: `ProveedorForm` (ModelForm), siguiendo la estructura de `ClienteForm`.
6. **Vistas — `inventario/views.py`**: `proveedor_list_crear` (listado + búsqueda + alta + paginación, siguiendo `cliente_list_crear`) y `proveedor_desactivar` (confirmación por GET y baja lógica por POST, siguiendo `cliente_desactivar`).
7. **Búsqueda**: `?q=` filtra por coincidencia parcial en nombre o número de documento, también normaliza caracteres de formato para buscar por documento, y agrega el ID exacto si `q` contiene solo dígitos; replica el criterio de `cliente_list_crear`.
8. **URLs — `inventario/urls.py`**: rutas nuevas.
9. **Templates — `templates/inventario/`**: `proveedor_list.html`, reutilizando la estructura visual de `cliente_list.html`, y `proveedor_confirm_delete.html` para la confirmación GET de la baja lógica.
10. **Navegación — `templates/base.html`**: agregar el link "Proveedores" en el sidebar, con resaltado activo para las rutas de listado y baja lógica, siguiendo el criterio por `request.resolver_match.url_name` de los demás enlaces.
11. **Admin — `inventario/admin.py`**: registrar `Proveedor`.

## Decisiones

- **Validación de documento compartida vía función, no vía modelo abstracto** — Se descartó una clase base abstracta (`PersonaBase` con `Cliente` y `Proveedor` heredando) porque son entidades conceptualmente distintas con relaciones futuras diferentes (`Pedido` vs `OrdenCompra`); compartir solo la validación evita acoplar los modelos sin necesidad.
- **Mismo patrón de listado+alta que `Cliente`** — Consistencia de UX y de código; quien ya conoce la pantalla de Clientes entiende la de Proveedores sin curva de aprendizaje.

## Riesgos

- **Romper los tests de `Cliente` al refactorizar** — Mitigado corriendo la suite completa de tests después de extraer `validar_documento`, antes de seguir con el resto del feature.