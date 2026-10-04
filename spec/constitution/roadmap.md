# Roadmap

_Orden y estado de las features. Es la vista de "qué hay hecho, qué toca ahora y qué viene". Cada entrada apunta a su carpeta en `features/`._

## Hecho ✅

_Features completadas, en orden de implementación._

1. **001 · Catálogo y Modelos Base** — Gestión de categorías y productos con validaciones, alertas de stock bajo y bajas lógicas para preservar el historial[cite: 2].
2. **002 · Movimientos e Historial** — Lógica centralizada y transaccional para registrar Entradas, Salidas y Ajustes físicos, junto con la auditoría cronológica unificada[cite: 2, 3].
3. **003 · Interfaz Dashboard** — Layout estructurado con barra lateral (sidebar), variables CSS y tarjetas limpias sin usar frameworks externos pesados[cite: 3].
4. **004 · Backups de Base de Datos** — Descarga segura de un snapshot SQLite completo para resguardar el estado del sistema y permitir restauración manual.
5. **007 · Clientes** — Padrón y gestión de clientes con normalización de DNI/CUIT por formato, búsqueda y baja lógica.
6. **008 · Pedidos de Venta** — Generación de pedidos confirmados, descuento de stock, correlativo anual, inmutabilidad y cancelación con reintegro de mercadería.
7. **009 · Generación de Pedido en PDF (Remito)** — Descarga de remitos PDF para pedidos con datos del cliente, operación y detalle de ítems.
8. **010 · Caja y Flujo de Efectivo** — Registro automático de ingresos y egresos por pedidos, egresos manuales y dashboard con saldo e historial.

> Nota de negocio: la validación del CUIT se mantiene en formato operativo (11 dígitos) y no se incorpora el algoritmo fiscal completo para no complejizar la lógica de datos del sistema actual.

> Estado funcional confirmado: las features 004, 007, 008 y 009 ya están operativas en la app actual.

## Siguiente 🔜

_Lo próximo a abordar. Idealmente una sola feature "en curso" a la vez._

9. **005 · Mejora de Inventario** — Optimización operativa del catálogo para facilitar carga y revisión rápida del stock y mejoras de UX en la gestión diaria.

## Backlog / ideas 💡

_Sin comprometer ni ordenar del todo. Ideas que respetan la constitución._

- **Mejoras de UX Operativa** — Agregar botones de atajo rápido (+ Ent, - Sal) directamente en cada fila de la tabla principal para agilizar la carga diaria[cite: 3].
- **Optimización de Formularios** — Implementar la cuadrícula (CSS Grid) en el alta de productos para hacerla más compacta visualmente[cite: 3].
- **Paginación e Iconografía** — Agregar paginación a la tabla de historial e inventario para cuando los registros crezcan, e íconos ligeros para fácil reconocimiento de botones[cite: 3].
- **Reporte de Stock** — Generación de resúmenes o exportaciones básicas del estado actual del depósito[cite: 2].

> Cada feature nueva se crea como `features/NNN-nombre-feature/` con `spec.md`, `plan.md` y `tasks.md` antes de tocar código.