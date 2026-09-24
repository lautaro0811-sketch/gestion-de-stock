# 003 · Backups de Base de Datos — Plan

## Enfoque

Aprovechar la arquitectura de SQLite que encapsula toda la base de datos en un único archivo físico (`db.sqlite3`). Implementaremos una vista que retorne este archivo mediante una respuesta HTTP de descarga directa, sin necesidad de librerías externas[cite: 2].

## Implementación

1. `inventario/views.py` — Crear controlador `descargar_backup` que ubique la ruta absoluta del archivo SQLite en `settings.DATABASES` y lo sirva usando `FileResponse`[cite: 2].
2. `inventario/urls.py` — Configurar una nueva ruta `/backup/` que apunte al controlador[cite: 2].
3. `templates/base.html` — Añadir el enlace/botón de "Descargar Copia de Seguridad" en la barra lateral de navegación para fácil acceso[cite: 2].

## Decisiones

- **Descarga directa de `.sqlite3`:** Se descartó exportar los datos a formatos como CSV o JSON para el backup, dado que el archivo nativo de SQLite es mucho más fácil de restaurar ante una emergencia simplemente reemplazándolo en la carpeta raíz del proyecto[cite: 2].

## Riesgos

- **Bloqueos de lectura del sistema operativo:** Windows podría bloquear el archivo si existe una transacción larga escribiendo. Mitigación: manejar posibles errores de I/O en la vista para advertir al usuario en caso de falla de permisos[cite: 2].