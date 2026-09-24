# Misión

Desarrollar un sistema de control de inventario local, simple y robusto, que garantice la trazabilidad absoluta de la mercadería sin sobrecargar al usuario ni al desarrollador con complejidades técnicas innecesarias[cite: 2]. 

## Qué construimos

Un sistema de gestión de stock local para productos de limpieza[cite: 2]. El producto permite registrar unidades entrantes y salientes, manteniendo el stock actual y un historial de movimientos inmutable[cite: 2].

1. **Catálogo de Productos y Categorías** — gestiona los artículos de limpieza, incluyendo su configuración de stock mínimo y la identificación visual de productos con stock bajo[cite: 2].
2. **Módulo de Movimientos** — centraliza el registro de entradas, salidas y ajustes de inventario mediante transacciones atómicas y seguras[cite: 2].
3. **Historial de Auditoría** — visualiza y filtra todos los movimientos históricos para rastrear exactamente cuándo y por qué cambió el stock de un producto[cite: 2].

## Para quién

- Un cliente particular que necesita controlar el inventario diario de sus productos de limpieza de manera sencilla y ágil[cite: 2].
- El desarrollador del sistema, que requiere que el código sea fácil de entender, mantener de forma personal y escalar de manera incremental[cite: 2].

## Principios

- **Trazabilidad estricta** — las modificaciones de stock deben realizarse exclusivamente mediante movimientos (entradas, salidas o ajustes), nunca editando manualmente el saldo actual desde la interfaz[cite: 2].
- **Integridad absoluta** — el sistema no debe permitir que el stock de un producto quede en negativo bajo ninguna circunstancia[cite: 2].
- **Preservación de datos** — no se deben eliminar físicamente productos que tengan un historial asociado; se debe utilizar un campo de estado para desactivarlos temporalmente (baja lógica)[cite: 2].
- **Simplicidad arquitectónica** — priorizar soluciones simples y mantenibles, utilizando Python, Django, SQLite y HTML/CSS nativo, agregando JavaScript únicamente cuando sea estrictamente necesario[cite: 2].

## Qué NO es

- No es un sistema alojado en la nube ni requiere servidores externos; es una aplicación diseñada inicialmente para funcionar de forma local en Windows[cite: 2].
- No es un ERP o sistema de facturación comercial; en esta versión inicial no maneja precios, compras, ventas, pagos, clientes ni proveedores[cite: 2].
- No es una aplicación de alta complejidad de infraestructura; deliberadamente no implementa API REST, Docker, bases de datos como PostgreSQL, ni frameworks de frontend reactivos como React o Vue[cite: 2].