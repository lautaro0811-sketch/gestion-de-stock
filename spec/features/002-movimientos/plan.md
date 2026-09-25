# 002 · Movimientos e Historial — Plan

## Enfoque

Delegar toda la lógica de validación e impacto de stock a una capa de servicios (`services.py`) aislada mediante transacciones atómicas, exponiendo estas funciones a través de una interfaz de formulario unificado para simplificar la experiencia operativa[cite: 2].

## Implementación

1. `inventario/services.py` — Creación de las funciones core (`registrar_entrada`, `registrar_salida`, `registrar_ajuste`) aseguradas con `transaction.atomic()`[cite: 2].
2. `inventario/forms.py` — Construcción de `MovimientoUnificadoForm` para capturar todos los datos en una sola pantalla[cite: 3].
3. `inventario/views.py` — Controladores `movimiento_crear` (conecta form y servicios) y `movimiento_historial` (gestiona la auditoría y filtros)[cite: 2, 3].
4. `templates/inventario/` — Desarrollo de las plantillas `movimiento_form.html` y `movimiento_historial.html` utilizando diseño de cuadrícula y etiquetas de colores[cite: 2, 3].
5. `inventario/urls.py` — Enrutamiento de las nuevas vistas[cite: 3].

## Decisiones

- **Lógica centralizada en services.py:** Garantiza el uso de bloqueos de fila de base de datos (`select_for_update()`); se descartó procesar la lógica en las vistas para evitar corromper datos ante peticiones concurrentes[cite: 2].
- **Formulario Unificado:** Se optó por una sola vista de registro para agilizar la carga operativa del usuario y limpiar la barra de navegación, en lugar de tener tres formularios y URLs separadas[cite: 2].
- **Ajuste por stock real:** Para los ajustes físicos, el operador ingresa lo que cuenta visualmente en estantería en lugar de calcular diferencias mentalmente; el backend calcula el delta exacto[cite: 2].

## Riesgos

- **Stock negativo:** Mitigado estructuralmente mediante el uso de campos enteros positivos en base de datos y validaciones explícitas de excepciones `ValidationError` que informan al usuario[cite: 2].