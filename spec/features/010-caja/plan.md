# 010 · Caja y Flujo de Efectivo — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Aplicaremos para el dinero las mismas reglas de inmutabilidad y atomicidad que usamos para el stock[cite: 11]. Se creará un modelo de registro histórico inmutable y toda la lógica de validación e impacto de saldos se centralizará en la capa de servicios (`services.py`). El saldo se calculará de forma dinámica para garantizar precisión matemática absoluta.

## Implementación

1. **Modelado de Datos (`inventario/models.py`)**: 
   - Crear el modelo `MovimientoCaja` con los campos: `fecha`, `tipo` (INGRESO, EGRESO), `monto` (`DecimalField` con 2 decimales), `concepto` (texto) y `pedido` (`ForeignKey` a `Pedido`, `null=True`, `blank=True`).
2. **Capa de Servicios (`inventario/services.py`)**:
   - Crear `registrar_ingreso_caja(monto, concepto, pedido=None)` y `registrar_egreso_caja(monto, concepto, pedido=None)`.
   - Modificar las funciones existentes `crear_pedido` y `cancelar_pedido` (de la feature 008) para que, dentro del mismo bloque `@transaction.atomic()`, invoquen estos nuevos servicios financieros.
3. **Formularios (`inventario/forms.py`)**:
   - Crear `EgresoCajaForm` con validación para asegurar que el monto ingresado sea mayor a cero.
4. **Controladores (`inventario/views.py`)**:
   - Crear `caja_dashboard`: calculará el saldo actual usando `MovimientoCaja.objects.aggregate(total_ingresos=Sum('monto', filter=Q(tipo='INGRESO')), total_egresos=Sum('monto', filter=Q(tipo='EGRESO')))` y listará el historial.
   - Crear `caja_egreso_crear`: manejará el POST del formulario de gastos manuales.
5. **Interfaz Gráfica (`templates/inventario/`)**:
   - Crear `caja_dashboard.html` y `caja_egreso_form.html`. Usar exclusivamente clases del `style.css` (ej. `.card`, `.badge-success`, `.badge-danger`)[cite: 11]. Agregar enlace en el sidebar de `base.html`.

## Decisiones

- **Clave Foránea opcional hacia `Pedido`** — Permite que la caja funcione ahora mismo para gastos diarios aislados, y deja la tabla preparada para agregarle un campo `compra_id` en el futuro cuando se integren los proveedores, centralizando todo el dinero en el mismo lugar.
- **Cálculo dinámico del Saldo (Agregación SQL)** — Se descartó tener un campo estático `saldo_actual` en un modelo de configuración. Calcular el saldo "al vuelo" sumando ingresos y restando egresos previene cualquier posible desincronización de datos por fallos de concurrencia.

## Riesgos

- **Egresos que dejan el saldo negativo** — Un egreso manual (o la cancelación de una venta vieja) podría dejar la caja temporalmente en negativo si no hay fondos suficientes registrados. 
  - *Mitigación*: Se permitirá la operación bajo la presunción de que el operador puso dinero de su bolsillo, pero el saldo se mostrará en color rojo (alerta visual) en el dashboard si cae por debajo de cero.