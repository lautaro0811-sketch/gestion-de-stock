# Roadmap

_Orden y estado de las features. Es la vista de "qué hay hecho, qué toca ahora y qué viene". Cada entrada apunta a su carpeta en `features/`._

## Hecho ✅

_Features completadas, en orden de implementación._

1. **001 · Catálogo y Modelos Base** — Gestión de categorías y productos con validaciones, alertas de stock bajo y bajas lógicas para preservar el historial[cite: 2].
2. **002 · Movimientos e Historial** — Lógica centralizada y transaccional para registrar Entradas, Salidas y Ajustes físicos, junto con la auditoría cronológica unificada[cite: 2, 3].
3. **003 · Interfaz Dashboard** — Layout estructurado con barra lateral (sidebar), variables CSS y tarjetas limpias sin usar frameworks externos pesados[cite: 3].
- **Paginación de Tablas** — Navegación paginada en listado de productos (15 por página) y en historial de auditoría (20 por página) con template tag que preserva filtros de búsqueda.

## Siguiente 🔜

_Lo próximo a abordar. Idealmente una sola feature "en curso" a la vez._

4. **004 · Backups de Base de Datos** — Herramienta o utilidad simple para descargar y generar copias de seguridad del archivo `db.sqlite3` para resguardar la información[cite: 2].

## Backlog / ideas 💡

_Sin comprometer ni ordenar del todo. Ideas que respetan la constitución._

- **Mejoras de UX Operativa** — Agregar botones de atajo rápido (+ Ent, - Sal) directamente en cada fila de la tabla principal para agilizar la carga diaria[cite: 3].
- **Optimización de Formularios** — Implementar la cuadrícula (CSS Grid) en el alta de productos para hacerla más compacta visualmente[cite: 3].
- **Iconografía** — Agregar íconos ligeros para fácil reconocimiento de botones.
- **Reporte de Stock** — Generación de resúmenes o exportaciones básicas del estado actual del depósito[cite: 2].
- **Mover estilos en línea a style.css (tech-stack.md)** — Limpiar atributos `style="..."` y colores en línea de las plantillas HTML para dar cumplimiento estricto a las convenciones de tech-stack.md.

> Cada feature nueva se crea como `features/NNN-nombre-feature/` con `spec.md`, `plan.md` y `tasks.md` antes de tocar código.