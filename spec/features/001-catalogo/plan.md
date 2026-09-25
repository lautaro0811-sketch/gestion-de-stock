# 001 · Catálogo y Modelos Base — Plan

_Cómo se implementa lo descrito en `spec.md`. Debe respetar la `constitution/`._

## Enfoque

Desarrollar el catálogo utilizando una única aplicación de Django (`inventario`) para mantener una arquitectura simple y fácil de mantener, evitando sobreingeniería desde el inicio[cite: 2]. La interfaz se construirá con plantillas HTML renderizadas desde el servidor, asegurando desde la base de datos y los formularios que el stock no pueda ser alterado manualmente[cite: 2].

## Implementación

1. **Configuración base — `core/settings.py`**: Registrar la aplicación `inventario`, configurar el idioma a español (`es-ar`), la zona horaria local y la ruta de la carpeta de plantillas (`templates/`)[cite: 2].
2. **Modelado de Datos — `inventario/models.py`**: Crear los modelos `Categoria` y `Producto`. El producto debe incluir campos para controlar `stock_actual` (entero positivo), `stock_minimo`, y un campo booleano `activo`[cite: 2].
3. **Registro en Admin — `inventario/admin.py`**: Exponer los modelos en el panel de administración de Django para pruebas rápidas, configurando `stock_actual` como campo de solo lectura (`readonly_fields`)[cite: 2].
4. **Formularios seguros — `inventario/forms.py`**: Crear `CategoriaForm` y `ProductoForm`. Excluir deliberadamente `stock_actual` del formulario de productos para cumplir con la regla de negocio[cite: 2, 3].
5. **Controladores del catálogo — `inventario/views.py`**: Implementar las vistas para listar productos (con soporte de búsqueda y filtro por stock crítico), crear nuevos productos, editar información descriptiva y aplicar la desactivación lógica (`producto_desactivar`)[cite: 2].
6. **Enrutamiento — `inventario/urls.py`**: Vincular las URLs semánticas a las vistas creadas[cite: 2].
7. **Plantillas visuales — `templates/inventario/`**: Crear los archivos HTML (`producto_list.html`, `producto_form.html`, `categoria_list.html`, etc.) integrándolos con `base.html` y los estilos centralizados[cite: 2].

## Decisiones

- **App única (`inventario`)** — para evitar la fragmentación prematura del código; se descartó la idea de crear múltiples aplicaciones (ej. separar productos de movimientos) porque agregaba complejidad innecesaria a un sistema de uso local[cite: 2].
- **Protección de dependencias (`on_delete=models.PROTECT`)** — garantiza la integridad referencial; si una categoría tiene productos asociados, no se permitirá eliminarla por error[cite: 2].
- **Baja Lógica (`activo = False`)** — preserva la consistencia de la base de datos. Se descartó la eliminación física (operación `DELETE`) de la base de datos para no dejar movimientos huérfanos ni romper el historial de auditoría de los artículos[cite: 2].
- **Restricción de edición de stock en formularios** — se excluyó el campo `stock_actual` en la interfaz visual y se bloqueó en el panel Admin; esto fuerza a que los saldos solo cambien a través de registros auditables, evitando ediciones "a mano"[cite: 2].

## Riesgos

- **Corrupción del saldo de inventario** — mitigado mediante el uso de `PositiveIntegerField` en la base de datos y la remoción explícita del campo `stock_actual` en las clases de `ModelForm`[cite: 2].
- **Problema de consultas "N+1" en listados** — al mostrar la categoría en la tabla de productos, Django podría hacer una consulta a SQLite por cada fila. Mitigado usando `.select_related("categoria")` en la vista `producto_list` para optimizar el rendimiento[cite: 2].