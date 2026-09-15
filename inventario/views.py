from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    CategoriaForm,
    MovimientoAjusteForm,
    MovimientoCantidadForm,
    ProductoForm,
)
from .models import Categoria, Movimiento, Producto
from .services import registrar_ajuste, registrar_entrada, registrar_salida


def producto_list(request):
    """Listado principal con filtros y buscador."""
    query = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "")
    solo_stock_bajo = request.GET.get("stock_bajo", "") == "1"

    # Solo mostramos productos activos
    productos = (
        Producto.objects.filter(activo=True)
        .select_related("categoria")
        .order_by("nombre")
    )

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)

    if solo_stock_bajo:
        # Filtramos en memoria usando la propiedad definida en el modelo
        productos = [p for p in productos if p.stock_bajo]

    categorias = Categoria.objects.all()

    context = {
        "productos": productos,
        "categorias": categorias,
        "query": query,
        "categoria_seleccionada": categoria_id,
        "solo_stock_bajo": solo_stock_bajo,
    }
    return render(request, "inventario/producto_list.html", context)


def producto_crear(request):
    """Alta de nuevo producto."""
    if request.method == "POST":
        form = ProductoForm(request.POST)
        if form.is_valid():
            producto = form.save()
            messages.success(
                request,
                f"Producto '{producto.nombre}' creado exitosamente con stock 0.",
            )
            return redirect("producto_list")
    else:
        form = ProductoForm()

    return render(
        request,
        "inventario/producto_form.html",
        {"form": form, "titulo": "Nuevo Producto"},
    )


def producto_editar(request, pk):
    """Edición de datos descriptivos del producto (sin alterar stock)."""
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        form = ProductoForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(
                request, f"Producto '{producto.nombre}' actualizado."
            )
            return redirect("producto_list")
    else:
        form = ProductoForm(instance=producto)

    return render(
        request,
        "inventario/producto_form.html",
        {
            "form": form,
            "producto": producto,
            "titulo": f"Editar: {producto.nombre}",
        },
    )


def producto_desactivar(request, pk):
    """Baja lógica de producto para preservar el historial de movimientos."""
    producto = get_object_or_404(Producto, pk=pk)

    if request.method == "POST":
        producto.activo = False
        producto.save(update_fields=["activo", "fecha_actualizacion"])
        messages.warning(
            request, f"Producto '{producto.nombre}' dado de baja del catálogo."
        )
        return redirect("producto_list")

    return render(
        request,
        "inventario/producto_confirm_delete.html",
        {"producto": producto},
    )


def categoria_list_crear(request):
    """Listado y creación rápida de categorías en una sola vista."""
    if request.method == "POST":
        form = CategoriaForm(request.POST)
        if form.is_valid():
            cat = form.save()
            messages.success(request, f"Categoría '{cat.nombre}' creada.")
            return redirect("categoria_list")
    else:
        form = CategoriaForm()

    categorias = Categoria.objects.all().order_by("nombre")
    return render(
        request,
        "inventario/categoria_list.html",
        {"form": form, "categorias": categorias},
    )

def movimiento_entrada(request):
    """Registro de movimientos de entrada."""
    if request.method == "POST":
        form = MovimientoCantidadForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data["producto"]
            cantidad = form.cleaned_data["cantidad"]
            observacion = form.cleaned_data["observacion"]

            try:
                registrar_entrada(producto.id, cantidad, observacion)
                messages.success(request, f"Se ingresaron {cantidad} u. de '{producto.nombre}'.")
                return redirect("producto_list")
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        form = MovimientoCantidadForm()

    context = {
        "form": form,
        "titulo": "Registrar Entrada de Stock",
        "tipo": "entrada",
    }
    return render(request, "inventario/movimiento_form.html", context)

def movimiento_salida(request):
    """Registro de movimientos de salida (egreso de stock)."""
    if request.method == "POST":
        form = MovimientoCantidadForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data["producto"]
            cantidad = form.cleaned_data["cantidad"]
            observacion = form.cleaned_data["observacion"]

            try:
                registrar_salida(producto.id, cantidad, observacion)
                messages.success(request, f"Se registraron {cantidad} u. de salida para '{producto.nombre}'.")
                return redirect("producto_list")
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        form = MovimientoCantidadForm()

    context = {
        "form": form,
        "titulo": "Registrar Salida de Stock",
        "tipo": "salida",
    }
    return render(request, "inventario/movimiento_form.html", context)


def movimiento_ajuste(request):
    """Registro de ajustes de stock por conteo físico."""
    if request.method == "POST":
        form = MovimientoAjusteForm(request.POST)
        if form.is_valid():
            producto = form.cleaned_data["producto"]
            stock_real = form.cleaned_data["stock_real"]
            observacion = form.cleaned_data["observacion"]

            try:
                registrar_ajuste(producto.id, stock_real, observacion)
                messages.success(request, f"Stock de '{producto.nombre}' ajustado a {stock_real} u.")
                return redirect("producto_list")
            except ValidationError as e:
                messages.error(request, e.message)
    else:
        form = MovimientoAjusteForm()

    context = {
        "form": form,
        "titulo": "Ajuste Físico de Stock",
        "tipo": "ajuste",
    }
    return render(request, "inventario/movimiento_form.html", context)


def movimiento_historial(request):
    """Listado auditable de todos los movimientos registrados."""
    tipo = request.GET.get("tipo", "").strip()
    producto_id = request.GET.get("producto", "").strip()

    # Optimizamos trayendo el producto en la misma consulta
    movimientos = Movimiento.objects.select_related("producto").order_by("-fecha")

    if tipo:
        movimientos = movimientos.filter(tipo=tipo)
    if producto_id:
        movimientos = movimientos.filter(producto_id=producto_id)

    productos = Producto.objects.all().order_by("nombre")

    context = {
        "movimientos": movimientos,
        "productos": productos,
        "tipos": Movimiento.TipoMovimiento.choices,
        "tipo_seleccionado": tipo,
        "producto_seleccionado": producto_id,
    }
    return render(request, "inventario/movimiento_historial.html", context)