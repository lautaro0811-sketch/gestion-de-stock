# 003 · Interfaz Dashboard — Plan

## Enfoque

Construir la estructura base de la interfaz de usuario con HTML5 semántico en `templates/base.html` y estilos centralizados en `static/css/style.css`, utilizando CSS nativo moderno (Flexbox y CSS Grid) para mantener la aplicación ligera, completamente autónoma y funcional offline.

## Implementación

1. **Estructura base — `templates/base.html`**: Definir el layout de dos columnas (barra lateral de navegación fija `<aside>` y área principal de contenido `<div class="main-wrapper">`).
2. **Variables de estilo — `static/css/style.css`**: Centralizar paleta tipográfica y cromática mediante variables CSS en `:root` (colores primario, advertencia, peligro, éxito, bordes y fondos).
3. **Componentes visuales**: Estilizar contenedores de tarjetas (`.card`), tablas responsivas (`table`, `.table-responsive`), botones unificados (`.btn`) y badges de estado (`.badge`).
4. **Mensajería**: Renderizar mensajes del framework `messages` de Django en la parte superior del contenedor principal.

## Decisiones

- **CSS nativo sin librerías externas**: Evita dependencias de CDNs externos o gestores de paquetes como npm, garantizando funcionamiento rápido y confiable en un entorno Windows de escritorio.
- **Barra lateral fija con scroll independiente**: Permite acceso constante a las secciones clave del sistema mientras se visualizan listas largas de inventario o movimientos.

## Riesgos

- **Inconsistencia de estilos por inline styles**: Mitigado centralizando selectores y variables en `style.css`.
