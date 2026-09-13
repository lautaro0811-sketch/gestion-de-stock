from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoriaForm, ProductoForm
from .models import Categoria, Producto


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