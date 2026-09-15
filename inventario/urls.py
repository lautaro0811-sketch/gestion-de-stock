from django.urls import path

from . import views

urlpatterns = [
    path("", views.producto_list, name="producto_list"),
    path("productos/nuevo/", views.producto_crear, name="producto_crear"),
    path(
        "productos/<int:pk>/editar/",
        views.producto_editar,
        name="producto_editar",
    ),
    path(
        "productos/<int:pk>/desactivar/",
        views.producto_desactivar,
        name="producto_desactivar",
    ),
    path("categorias/", views.categoria_list_crear, name="categoria_list"),
    path("movimientos/entrada/", views.movimiento_entrada, name= 'movimiento_entrada'),
    path("movimientos/salida/", views.movimiento_salida, name = 'movimiento_salida'),
    path("movimientos/ajuste/", views.movimiento_ajuste, name = 'movimiento_ajuste'),
    path("movimientos/", views.movimiento_historial, name = 'movimiento_historial'),
    
]