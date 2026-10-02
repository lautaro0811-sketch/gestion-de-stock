# 008 · Pedidos de Venta — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Construiremos los modelos `Pedido` y `PedidoItem` dentro de la misma app `inventario` para evitar fragmentación prematura y cruce de dependencias complejas[cite: 5]. Utilizaremos la robustez comprobada de `services.py`[cite: 5]: el pedido actuará como un orquestador que llamará iterativamente a `registrar_salida` y `registrar_entrada` envolviendo todo en un bloque `transaction.atomic()`[cite: 5].

## Implementación

_Pasos técnicos concretos, en orden. Indica los archivos/módulos que se tocan._

1. **Modelos Base (`inventario/models.py`)**: 
   - Agregar `precio_unitario` a `Producto`.
   - Crear el modelo `Pedido` (`numero_operacion`, `cliente`, `fecha`, `estado` = CONFIRMADO/CANCELADO).
   - Crear el modelo `PedidoItem` (`pedido`, `producto`, `cantidad`, `precio_unitario`).
   - Agregar `pedido = models.ForeignKey(Pedido, null=True, blank=True)` a `Movimiento`.
2. **Servicios Core (`inventario/services.py`)**:
   - Crear función `crear_pedido(cliente_id, items_data)`. Dentro de un `transaction.atomic()`, calcular el próximo número correlativo, crear el `Pedido` y los `PedidoItem`, y llamar a `registrar_salida` por cada uno asociándoles el nuevo ID del pedido.
   - Crear función `cancelar_pedido(pedido_id)`. Cambiar estado a CANCELADO y llamar iterativamente a `registrar_entrada` para devolver el stock asociando el mismo ID de pedido.
   - Modificar las firmas de `registrar_entrada` y `registrar_salida` para que acepten un argumento opcional `pedido_id`.
3. **Formularios (`inventario/forms.py`)**:
   - Crear `PedidoForm` y un inline formset para los `PedidoItem` para procesar múltiples artículos en la misma vista.
4. **Controladores (`inventario/views.py`)**:
   - Crear vistas `pedido_list` (historial de ventas), `pedido_detalle` (solo lectura) y `pedido_crear`.
   - Crear vista `pedido_cancelar` que ejecute el servicio de anulación.
5. **Documentación Extendida (`spec/features/001-catalogo/spec.md`)**:
   - Registrar retroactivamente el campo `precio_unitario` documentándolo como una extensión proveniente de la feature 008.

## Decisiones

_Elecciones de diseño relevantes y su justificación. Alternativas descartadas y por qué._

- **Vincular el ID de Pedido a `Movimiento` con `null=True`** — Mantiene la separación de conceptos: permite que los ingresos por compra, movimientos manuales iniciales o ajustes físicos por error sigan funcionando sin requerir obligatoriamente estar atados a una Venta[cite: 5].
- **No permitir edición de Pedidos** — Modificar un pedido existente implicaría calcular deltas complejos de stock (entradas o salidas compensatorias parciales) que abren la puerta a bugs críticos. Se descartó en favor de la inmutabilidad: si te equivocás, lo cancelás y creás uno nuevo.
- **Asignación de número secuencial en Python (select_for_update) vs base de datos** — Usaremos una consulta `select_for_update()` a una tabla contadora o calcularemos el `MAX(id)` del año en curso dentro de la transacción atómica, descartando el autoincremental por defecto de SQLite, para garantizar el formato AÑO-XXXX sin saltos ni huecos visibles para el cliente.

## Riesgos

_Qué puede salir mal o requerir cuidado, y cómo se mitiga._

- **Colisiones en el número de operación** — Si dos usuarios o pestañas generan un pedido en el mismo exacto milisegundo, podrían obtener el mismo número. Se mitiga calculando y asignando el número de operación estrictamente dentro del contexto `@transaction.atomic` justo antes del `.save()`.
- **Inconsistencia de formularios dinámicos (Formsets)** — Añadir múltiples filas de ítems en el frontend requiere JavaScript básico para clonar los campos. Se mitiga usando una plantilla limpia o un script mínimo y local (Vanilla JS), sin agregar dependencias como React.