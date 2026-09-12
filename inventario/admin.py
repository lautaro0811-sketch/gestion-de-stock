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
    list_display = ("id", "producto", "tipo", "cantidad", "fecha")
    list_filter = ("tipo", "fecha")
    search_fields = ("producto__nombre", "observacion")
    # El historial no debe editarse ni modificarse arbitrariamente
    readonly_fields = ("fecha",)