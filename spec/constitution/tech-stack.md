# Sistema para control de Stock
Sistema de gestión de inventario de productos de limpieza para un cliente particular, diseñado inicialmente como aplicación local en Windows. Permite registrar unidades entrantes, salientes y ajustes físicos, manteniendo un historial de movimientos inmutable.

## Stack
- Lenguaje: Python
- Framework / runtime: Django
- Base de datos: SQLite
- Frontend: HTML/CSS nativo (sin frameworks pesados) y JavaScript únicamente cuando sea necesario

## Entorno y Directorio de Trabajo
- Directorio raíz del proyecto Django: `gestion_stock/` (todos los comandos de Django y Python deben ejecutarse dentro de esta carpeta: `cd gestion_stock`).
- Activación del entorno virtual (Windows):
  - PowerShell: `.\venv\Scripts\Activate.ps1`
  - CMD: `venv\Scripts\activate.bat`

## Comandos (dentro de `gestion_stock/`)
- `python manage.py runserver` — arranca el servidor en local
- `python manage.py makemigrations` — prepara los cambios en la base de datos
- `python manage.py migrate` — aplica los cambios a la base de datos SQLite
- `python manage.py shell` — abre la consola interactiva para pruebas de lógica de negocio
- `python manage.py test inventario` — ejecuta la suite de pruebas unitarias y de integración
- `pip install -r requirements.txt` — instala las dependencias del proyecto

## Estructura del proyecto
- `gestion_stock/` — Directorio que contiene el proyecto Django.
  - `core/` — Configuración general del proyecto, incluyendo `settings.py` y `urls.py` globales.
  - `inventario/` — App principal que contiene los modelos (`Categoria`, `Producto`, `Movimiento`), vistas, formularios, capa de servicios y tests (`tests.py`).
  - `templates/inventario/` — Plantillas HTML con diseño basado en Dashboard (barra lateral y contenido).
  - `static/css/` — Estilos del sistema centralizados en `style.css` utilizando variables en `:root`.
  - `requirements.txt` — Dependencias del proyecto fijadas para reproducibilidad.

## Convenciones
- Lógica de stock centralizada: Todo cambio en el stock debe pasar por `inventario/services.py` usando `transaction.atomic()` y `select_for_update()` para asegurar la integridad de los datos. *(Nota: en SQLite `select_for_update()` no bloquea filas a nivel de registro; la consistencia se garantiza con `transaction.atomic()`. Se mantiene la convención para una futura migración a PostgreSQL).*
- Baja de productos: Utilizar siempre una baja lógica cambiando `activo = False` para no romper el historial de movimientos asociado al producto.
- Manejo de estilos: Toda la paleta de colores y variables estructurales debe ir en el archivo CSS centralizado, promoviendo un diseño limpio y moderno.
- Notificaciones: Usar el framework `messages` de Django para capturar y mostrar validaciones y confirmaciones de acciones en la interfaz de usuario.
- Dependencias: Si se instala algún paquete adicional necesario, mantener actualizado el archivo `requirements.txt` (`pip freeze > requirements.txt`).

## No hagas
- No implementar en esta versión herramientas complejas como API REST, Docker, PostgreSQL o frameworks como React/Vue.
- No permitir que el stock de un producto quede en negativo; validar siempre las salidas.
- No permitir la edición manual del campo `stock_actual` desde la interfaz; todas las modificaciones deben generarse registrando Entradas, Salidas o Ajustes.
- No utilizar estilos CSS en línea ni colores hardcodeados directamente dentro de las etiquetas HTML de las plantillas.

## Flujo de trabajo
- Antes de una tarea no trivial, propón un plan y espera mi OK.
- Una tarea a la vez; al terminar, dime qué cambiaste para que lo revise.
- Si no estás seguro al 80%, pregunta. No inventes.
- **Testing**: Ejecutar siempre `python manage.py test inventario` antes y después de hacer cambios en modelos o en la lógica de negocio para certificar que todas las pruebas pasen y no haya regresiones.

## Documentación
- Ante cualquier duda sobre los requerimientos, consulta el archivo Sistema para control de Stock.

