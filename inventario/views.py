from datetime import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import CategoriaForm, MovimientoUnificadoForm, ProductoForm
from .models import Categoria, Movimiento, Producto
from .services import registrar_ajuste, registrar_entrada, registrar_salida


# --- PRODUCTOS ---
def producto_list(request):
    query = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    solo_stock_bajo = request.GET.get("stock_bajo") == "1"

    productos = Producto.objects.filter(activo=True).select_related("categoria")

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    categorias = Categoria.objects.all()

    if solo_stock_bajo:
        productos = [p for p in productos if p.stock_bajo]

    return render(
        request,
        "inventario/producto_list.html",
        {
            "productos": productos,
            "categorias": categorias,
            "query": query,
            "categoria_seleccionada": categoria_id,
            "solo_stock_bajo": solo_stock_bajo,
        },
    )


def producto_crear(request):
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(request, f"Producto '{producto.nombre}' creado exitosamente.")
            return redirect("producto_list")
    else:
        form = ProductoForm()

    return render(request, "inventario/producto_form.html", {"form": form, "titulo": "Nuevo Producto"})


def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Producto '{producto.nombre}' actualizado.")
            return redirect("producto_list")
    else:
        form = ProductoForm(instance=producto)

    return render(request, "inventario/producto_form.html", {"form": form, "titulo": "Editar Producto"})


def producto_desactivar(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == "POST":
        producto.activo = False
        producto.save(update_fields=["activo"])
        messages.success(request, f"Producto '{producto.nombre}' dado de baja.")
    return redirect("producto_list")


# --- CATEGORÍAS ---
def categoria_list_crear(request):
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            categoria = form.save()
            messages.success(request, f"Categoría '{categoria.nombre}' creada.")
            return redirect("categoria_list")
    else:
        form = CategoriaForm()

    categorias = Categoria.objects.all()
    return render(
        request,
        "inventario/categoria_list.html",
        {"categorias": categorias, "form": form},
    )


# --- MOVIMIENTOS ---
def movimiento_crear(request):
    """Vista unificada para registrar Entrada, Salida o Ajuste."""
    producto_id_param = request.GET.get("producto")

    if request.method == "POST":
        form = MovimientoUnificadoForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data["producto"]
            fecha_date = form.cleaned_data["fecha"]
            tipo = form.cleaned_data["tipo"]
            cantidad = form.cleaned_data["cantidad"]
            observacion = form.cleaned_data["observacion"]

            hora_actual = timezone.now().time()
            fecha_completa = timezone.make_aware(
                datetime.combine(fecha_date, hora_actual)
            )

            try:
                if tipo == "ENTRADA":
                    registrar_entrada(producto.id, cantidad, observacion, fecha=fecha_completa)
                    messages.success(request, f"Entrada registrada: +{cantidad} u. de '{producto.nombre}'.")
                elif tipo == "SALIDA":
                    registrar_salida(producto.id, cantidad, observacion, fecha=fecha_completa)
                    messages.success(request, f"Salida registrada: -{cantidad} u. de '{producto.nombre}'.")
                elif tipo == "AJUSTE":
                    registrar_ajuste(producto.id, cantidad, observacion, fecha=fecha_completa)
                    messages.success(request, f"Stock de '{producto.nombre}' ajustado a {cantidad} u.")

                return redirect("movimiento_historial")

            except ValidationError as e:
                messages.error(request, e.message)
    else:
        initial_data = {}
        if producto_id_param:
            initial_data["producto"] = producto_id_param
        form = MovimientoUnificadoForm(initial=initial_data)

    return render(request, "inventario/movimiento_form.html", {"form": form})


def movimiento_historial(request):
    tipo_filtro = request.GET.get("tipo", "").strip()
    producto_filtro = request.GET.get("producto", "").strip()

    movimientos = Movimiento.objects.select_related("producto").all()

    if tipo_filtro:
        movimientos = movimientos.filter(tipo=tipo_filtro)
    if producto_filtro:
        movimientos = movimientos.filter(producto_id=producto_filtro)

    productos = Producto.objects.all().order_by("nombre")

    return render(
        request,
        "inventario/movimiento_historial.html",
        {
            "movimientos": movimientos,
            "productos": productos,
            "tipos": Movimiento.TipoMovimiento.choices,
            "tipo_seleccionado": tipo_filtro,
            "producto_seleccionado": producto_filtro,
        },
    )