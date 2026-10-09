# 016 · Filtros en Caja — Plan

## Enfoque

Se agregan parámetros GET a `caja_dashboard` (`periodo`, `mes`, `anio`, `tipo`) que determinan el rango de fechas y el tipo a aplicar sobre el queryset de `MovimientoCaja`. Las tarjetas (Ingresos/Egresos/Saldo) se calculan SOLO con el filtro de período aplicado; la tabla de historial se calcula con período + tipo combinados. Se reutiliza el mismo mecanismo ya usado en 005 para que los links de filtro no dupliquen query params entre sí.

## Implementación

1. **Vista — `inventario/views.py` (`caja_dashboard`)**:
   - Leer `periodo` (valores válidos: `todo` [default], `mes_actual`, `anio_actual`, `mes_especifico`), y si es `mes_especifico`, leer `mes` (1-12) y `anio` (entero), validando ambos con try/except — si son inválidos, caer a `periodo=todo`.
   - Leer `tipo` (valores válidos: vacío/`todos` [default], `INGRESO`, `EGRESO`); cualquier otro valor se ignora.
   - Construir `queryset_periodo = MovimientoCaja.objects.all()` filtrado por rango de fechas según `periodo` (sin filtrar por tipo).
   - Calcular `total_ingresos`, `total_egresos` y `saldo` a partir de `queryset_periodo` (reutilizando el mismo patrón de `aggregate` + `Sum` con filtro por `tipo` ya usado hoy).
   - Construir `queryset_tabla = queryset_periodo` y, si `tipo` no es vacío, agregar `.filter(tipo=tipo)` solo para la tabla, sin tocar los agregados ya calculados.
   - Pasar al contexto: `total_ingresos`, `total_egresos`, `saldo`, `movimientos` (la tabla filtrada), `periodo`, `mes`, `anio`, `tipo`, y un booleano `mostrar_saldo_periodo` (`periodo != "todo"`) para controlar el título de la tarjeta.
2. **Template — `caja_dashboard.html`**:
   - Agregar los tres botones de período y el selector de mes+año específico (un `<select>` de mes y un `<select>` o input de año), todos construidos como links que preservan el filtro de `tipo` actual.
   - Agregar el selector de tipo (podría ser un `<select>` con auto-submit vía un pequeño form, o tres links, a elección del que implemente — mantener consistencia visual con el filtro de categoría ya existente en `producto_list.html`).
   - Condicionar el título de la tarjeta de saldo: `{% if mostrar_saldo_periodo %}Saldo del período{% else %}Saldo actual{% endif %}`.
3. **Helper de query params**: antes de escribir los links nuevos, revisar cómo quedó resuelta en 005 la construcción de `href` sin duplicar `orden`/`dir`, y aplicar el mismo mecanismo acá para `periodo`/`mes`/`anio`/`tipo`.

## Decisiones

- **El filtro de tipo no afecta los agregados** — Si filtrás por tipo, el saldo seguiría siendo el saldo real del período (ingresos menos egresos), y la tabla de abajo muestra solo lo que pediste ver. Evita que "Egresos: $0" aparezca junto a un saldo igual a los ingresos, que sería engañoso.
- **Etiqueta dinámica de la tarjeta de saldo** — Evita que alguien confunda "Saldo del período" (recalculado) con la plata real disponible hoy, que solo se ve con `periodo=todo`.
- **Botones rápidos + selector aparte para meses pasados** — Decisión ya tomada por el usuario; cubre tanto el caso más común (mes actual, año actual) como la necesidad de revisar un mes específico anterior.

## Riesgos

- **Reintroducir el bug de duplicación de query params** — Ya nos pasó una vez con el ordenamiento de columnas en 005 y se corrigió. Mitigado reutilizando exactamente el mismo mecanismo ya probado, no uno nuevo.
- **Año fuera de rango o sin movimientos** — Si se elige un año/mes sin ningún `MovimientoCaja`, las tarjetas deben mostrar $0 en todo, no romper.