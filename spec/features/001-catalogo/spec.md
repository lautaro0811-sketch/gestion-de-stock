# 001 · Catálogo y Modelos Base

**Estado:** implementado ✅

## Qué hace

Permite al usuario gestionar las categorías y el catálogo principal de los productos de limpieza[cite: 2]. Desde una interfaz visual, el usuario puede dar de alta nuevos artículos, organizarlos, visualizar el estado actual del inventario, realizar búsquedas y configurar alertas de stock mínimo[cite: 2].

## Por qué

Es el módulo fundacional del sistema. Sin un catálogo de productos estructurado, es imposible registrar los movimientos físicos de la mercadería ni mantener la trazabilidad del inventario. Establecer estos modelos base garantiza que todas las futuras operaciones de stock se asocien a artículos reales y consistentes[cite: 2].

## Criterios de aceptación

_Condiciones verificables que deben cumplirse para dar la feature por terminada. Redacta cada una de forma que se pueda comprobar con un sí/no. Marca `[x]` al cumplirse._

- [x] El sistema permite registrar categorías y productos garantizando que los nombres sean únicos para evitar duplicidad[cite: 2].
- [x] Al crear o editar un producto, el campo de stock actual está protegido (excluido) para impedir que el usuario lo modifique manualmente[cite: 2].
- [x] El listado principal muestra únicamente los productos activos y señala visualmente aquellos artículos cuyo stock actual está por debajo o igual al stock mínimo configurado[cite: 2].
- [x] Existe un buscador que permite filtrar la tabla de productos por nombre o descripción, además de un filtro para mostrar exclusivamente el stock en estado crítico[cite: 2].
- [x] La acción de "eliminar" un producto en realidad ejecuta una baja lógica (cambia el campo `activo` a falso), garantizando que el artículo desaparezca del catálogo sin borrar físicamente el registro de la base de datos[cite: 2].

## Fuera de alcance

_Lo que esta feature NO incluye, para evitar que crezca. Si algo se difiere, enlaza a dónde (roadmap/backlog)._

- La alteración de los saldos de inventario. El registro operativo de Entradas, Salidas y Ajustes de stock se implementará en la feature `002-movimientos`[cite: 2].
- La vista de auditoría cronológica (historial de movimientos), que también pertenece al módulo de movimientos[cite: 2].