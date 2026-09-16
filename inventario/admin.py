from django.contrib import admin

from .models import Categoria, Movimiento, Producto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nombre",
        "categoria",
        "stock_actual",
        "stock_minimo",
        "alerta_stock_bajo",
        "activo",
    )
    list_filter = ("activo", "categoria")
    search_fields = ("nombre", "descripcion")
    # Regla: No permitir la edición manual de stock_actual desde el formulario
    readonly_fields = ("stock_actual", "fecha_creacion", "fecha_actualizacion")

    @admin.display(boolean=True, description="Alerta: Stock crítico")
    def alerta_stock_bajo(self, obj):
        return obj.stock_bajo

@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fecha",
        "producto",
        "tipo",
        "cantidad",
        "stock_anterior",
        "stock_posterior",
        "created_by",
    )
    list_filter = ("tipo", "fecha", "created_by")
    search_fields = ("producto__nombre", "observacion", "created_by__username")
    # Todos los campos son de sólo lectura en caso de inspección
    readonly_fields = (
        "id",
        "fecha",
        "producto",
        "tipo",
        "cantidad",
        "stock_anterior",
        "stock_posterior",
        "created_by",
        "observacion",
    )
    # Deshabilitar acciones masivas de eliminación
    actions = None

    def has_add_permission(self, request):
        """Los movimientos solo se generan a través de servicios de inventario."""
        return False

    def has_change_permission(self, request, obj=None):
        """Los movimientos son registros inmutables de auditoría."""
        return False

    def has_delete_permission(self, request, obj=None):
        """No se permite eliminar registros históricos de movimientos."""
        return False