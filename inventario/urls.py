from django.urls import path

from . import views

urlpatterns = [
    path("", views.producto_list, name="producto_list"),
    path("productos/nuevo/", views.producto_crear, name="producto_crear"),
    path("productos/<int:pk>/editar/", views.producto_editar, name="producto_editar"),
    path("productos/<int:pk>/desactivar/", views.producto_desactivar, name="producto_desactivar"),
    path("categorias/", views.categoria_list_crear, name="categoria_list"),
    path("clientes/", views.cliente_list_crear, name="cliente_list"),
    path("clientes/<int:pk>/desactivar/", views.cliente_desactivar, name="cliente_desactivar"),
    path("proveedores/", views.proveedor_list_crear, name="proveedor_list"),
    path("proveedores/<int:pk>/desactivar/", views.proveedor_desactivar, name="proveedor_desactivar"),
    path("pedidos/", views.pedido_list, name="pedido_list"),
    path("pedidos/nuevo/", views.pedido_crear, name="pedido_crear"),
    path("pedidos/<int:pk>/", views.pedido_detalle, name="pedido_detalle"),
    path("pedidos/<int:pk>/pdf/", views.pedido_pdf_view, name="pedido_pdf"),
    path("pedidos/<int:pk>/cancelar/", views.pedido_cancelar, name="pedido_cancelar"),
    path("movimientos/", views.movimiento_historial, name="movimiento_historial"),
    path("movimientos/nuevo/", views.movimiento_crear, name="movimiento_crear"),
    path("backup/", views.descargar_backup, name="descargar_backup"),
    path("exportar/", views.export_csv, name="export_csv"),
    path("caja/", views.caja_dashboard, name="caja_dashboard"),
    path("caja/egreso/", views.caja_egreso_crear, name="caja_egreso_crear"),
]