# 002 · Movimientos e Historial

**Estado:** implementado ✅

## Qué hace

Permite registrar entradas, salidas y ajustes físicos de mercadería mediante un formulario unificado, y consultar el historial completo de auditoría del inventario[cite: 2].

## Por qué

Centraliza la alteración de stock para evitar ediciones manuales inseguras por parte del usuario y garantizar una trazabilidad absoluta de todos los movimientos de los productos[cite: 2].

## Criterios de aceptación

_Condiciones verificables que deben cumplirse para dar la feature por terminada._

- [x] El formulario unificado permite seleccionar Entradas, Salidas y Ajustes físicos[cite: 2].
- [x] El sistema rechaza cualquier salida que intente dejar el stock disponible en valores negativos[cite: 2].
- [x] Toda operación se registra en el historial con fecha, tipo de movimiento, cantidad y observaciones opcionales[cite: 2].
- [x] Se permite cargar movimientos con fechas retroactivas o personalizadas editando el campo de fecha[cite: 2].
- [x] La tabla de historial incluye filtros funcionales por tipo de operación y por producto[cite: 2].

## Fuera de alcance

- Atajos rápidos de carga de stock integrados directamente en la tabla del catálogo principal (se implementará en la mejora visual del dashboard)[cite: 3].