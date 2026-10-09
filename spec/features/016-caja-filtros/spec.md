# 016 · Filtros en Caja

**Estado:** propuesta

## Qué hace

Agrega filtros al Dashboard de Caja: por período (Todo / Este mes / Este año / un mes y año específicos del pasado) y por tipo de movimiento (Todos / solo Ingresos / solo Egresos). El período filtrado recalcula las tarjetas de Ingresos, Egresos y Saldo; el filtro de tipo solo afecta qué filas se muestran en la tabla del historial, sin alterar los totales.

## Por qué

Hoy Caja solo muestra el acumulado histórico completo, sin forma de ver "cuánto entró/salió este mes" o de revisar un mes anterior puntual. Es información que cualquiera que maneje una caja necesita consultar habitualmente.

## Criterios de aceptación

- [ ] Existen botones de período: "Todo" (default), "Este mes", "Este año".
- [ ] Existe un selector adicional para elegir un mes y año específicos del pasado (ej. "Septiembre 2026"), independiente de los tres botones rápidos.
- [ ] Existe un selector de tipo: "Todos" (default), "Ingresos", "Egresos".
- [ ] Al aplicar un filtro de período distinto de "Todo", las tarjetas de Ingresos, Egresos y Saldo se recalculan usando solo los movimientos de ese período.
- [ ] El filtro de tipo NO afecta el cálculo de las tarjetas (Ingresos/Egresos/Saldo siempre consideran ambos tipos dentro del período elegido); solo filtra qué filas aparecen en la tabla "Historial de movimientos".
- [ ] Cuando el período filtrado es distinto de "Todo", la tarjeta de saldo cambia su título de "Saldo actual" a "Saldo del período".
- [ ] Los filtros de período y tipo se pueden combinar entre sí sin perderse (cambiar uno no resetea el otro), usando el mismo criterio de preservación de query params ya usado en el ordenamiento de `producto_list` (005), evitando duplicar parámetros en la URL.
- [ ] Si se pasan parámetros de filtro inválidos (mes fuera de 1-12, año no numérico, tipo que no sea INGRESO/EGRESO), la vista los ignora y usa el valor por defecto, sin lanzar excepción.

## Fuera de alcance

- Rango de fechas libre (desde/hasta) con calendario. Se usan los botones rápidos y el selector de mes+año específico.
- Filtrar el historial por concepto, por pedido o por orden de compra puntual (queda para una revisión futura si hace falta).
- Exportar el historial filtrado a CSV (se podría replicar el patrón de exportación ya usado en Inventario en una feature posterior).