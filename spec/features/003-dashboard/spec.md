# 003 · Interfaz Dashboard

**Estado:** implementado ✅

## Qué hace

Provee la estructura visual principal del sistema tipo Dashboard, incluyendo una barra de navegación lateral fija (sidebar), el área de contenido principal, la visualización de mensajes y alertas del sistema (notificaciones flash) y la integración de variables CSS para consistencia estética sin recurrir a frameworks externos.

## Por qué

Ofrece una interfaz ágil, profesional y fácil de usar para operar localmente el catálogo, registrar movimientos y auditar el historial sin distracciones visuales ni dependencias complejas.

## Criterios de aceptación

- [x] Layout principal estructurado con barra lateral fija (`sidebar`) y contenedor central adaptable.
- [x] Barra de navegación semántica que enlaza a las vistas clave (Inventario, Nuevo Producto, Registrar Movimiento, Historial, Categorías) resaltando la sección activa.
- [x] Bloque de visualización de notificaciones del sistema integrando el framework `django.contrib.messages`.
- [x] Hoja de estilos centralizada (`static/css/style.css`) con variables CSS en `:root` para colores de estado, espaciados y tipografía de sistema.

## Fuera de alcance

- Frameworks CSS o JS pesados (Bootstrap, Tailwind, React, Vue).
- Modo oscuro y personalización dinámica de temas.
