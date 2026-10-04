# 010 · Caja y Flujo de Efectivo — Tareas

_Checklist accionable derivada del `plan.md`. Tareas pequeñas y concretas; marca `[x]` al completarlas._

- [x] Crear el modelo `MovimientoCaja` en `models.py` asegurando el uso de `DecimalField` y la FK opcional a `Pedido`.
- [x] Generar y ejecutar las migraciones correspondientes (`makemigrations`, `migrate`).
- [x] Implementar `registrar_ingreso_caja` y `registrar_egreso_caja` en `services.py` asegurando integridad transaccional[cite: 11].
- [x] Integrar la llamada a `registrar_ingreso_caja` dentro de la función `crear_pedido` (feature 008).
- [x] Integrar la llamada a `registrar_egreso_caja` dentro de la función `cancelar_pedido` (feature 008).
- [x] Crear `EgresoCajaForm` en `forms.py`.
- [x] Construir la vista `caja_dashboard` en `views.py`, implementando la lógica de agregación matemática (`Sum`) para calcular el saldo en tiempo real.
- [x] Construir la vista `caja_egreso_crear` en `views.py`.
- [x] Registrar las nuevas rutas en `urls.py`.
- [x] Desarrollar `caja_dashboard.html` y `caja_egreso_form.html` respetando la prohibición de estilos CSS en línea[cite: 11].
- [x] Añadir el acceso a "Caja" en el menú de navegación (`base.html`).
- [x] Escribir tests unitarios en `tests.py` que comprueben: cálculo exacto del saldo, registro automático de ingresos/egresos al manipular pedidos, y la creación de un egreso manual.
- [x] Validar contra los criterios de aceptación de `spec.md`.
- [x] Mover la feature a "Hecho" en `../../constitution/roadmap.md`.