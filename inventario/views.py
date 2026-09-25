from datetime import datetime

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
import csv
from django.http import HttpResponse

from .forms import (
    CategoriaForm,
    MovimientoUnificadoForm,
    ProductoCrearForm,
    ProductoEditarForm,
)
from .models import Categoria, Movimiento, Producto
from .services import registrar_ajuste, registrar_entrada, registrar_salida


# --- PRODUCTOS ---
def producto_list(request):
    query = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    solo_stock_bajo = request.GET.get("stock_bajo") == "1"

    # Ordering parameters
    orden = request.GET.get("orden")
    dir_param = request.GET.get("dir", "asc")
    whitelist = {
        "nombre": "nombre",
        "categoria": "categoria__nombre",
        "stock_actual": "stock_actual",
        "stock_minimo": "stock_minimo",
    }
    if orden in whitelist:
        order_field = whitelist[orden]
        if dir_param == "desc":
            order_field = f"-{order_field}"
        productos = Producto.objects.filter(activo=True).select_related("categoria").order_by(order_field)
    else:
        productos = Producto.objects.filter(activo=True).select_related("categoria")

    if query:
        productos = productos.filter(
            Q(nombre__icontains=query) | Q(descripcion__icontains=query)
        )
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if solo_stock_bajo:
        productos = productos.filter(stock_actual__lte=F("stock_minimo"))

    categorias = Categoria.objects.all()
    paginator = Paginator(productos, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventario/producto_list.html",
        {
            "productos": page_obj,
            "page_obj": page_obj,
            "categorias": categorias,
            "query": query,
            "categoria_seleccionada": categoria_id,
            "solo_stock_bajo": solo_stock_bajo,
            "orden": orden,
            "dir": dir_param,
        },
    )



@transaction.atomic
def producto_crear(request):
    if request.method == "POST":
        form = ProductoCrearForm(request.POST)
        if form.is_valid():
            producto = form.save(commit=False)
            producto.stock_actual = 0  # Garantizamos que nazca en 0
            producto.save()

            stock_inicial = form.cleaned_data.get("stock_inicial") or 0
            if stock_inicial > 0:
                usuario = request.user if request.user.is_authenticated else None
                registrar_entrada(
                    producto_id=producto.id,
                    cantidad=stock_inicial,
                    observacion="Stock inicial de apertura de producto",
                    usuario=usuario,
                )

            messages.success(request, f"Producto '{producto.nombre}' creado exitosamente.")
            return redirect("producto_list")
    else:
        form = ProductoCrearForm()

    return render(request, "inventario/producto_form.html", {"form": form, "titulo": "Nuevo Producto"})


def producto_editar(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == "POST":
        form = ProductoEditarForm(request.POST, instance=producto)
        if form.is_valid():
            form.save()
            messages.success(request, f"Producto '{producto.nombre}' actualizado.")
            return redirect("producto_list")
    else:
        form = ProductoEditarForm(instance=producto)

    return render(
        request,
        "inventario/producto_form.html",
        {"form": form, "titulo": "Editar Producto", "producto": producto},
    )


def producto_desactivar(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    if request.method == "POST":
        producto.activo = False
        producto.save(update_fields=["activo", "fecha_actualizacion"])
        messages.success(request, f"Producto '{producto.nombre}' dado de baja correctamente.")
        return redirect("producto_list")

    return render(request, "inventario/producto_confirm_delete.html", {"producto": producto})


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
@transaction.atomic
def movimiento_crear(request):
    """Vista unificada para registrar Entrada, Salida o Ajuste."""
    producto_id_param = request.GET.get("producto")
    tipo_param = request.GET.get("tipo")
    initial_data = {}
    if producto_id_param:
        try:
            initial_data["producto"] = int(producto_id_param)
        except (ValueError, TypeError):
            pass  # ignore invalid product id
    if tipo_param:
        initial_data["tipo"] = tipo_param
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
            usuario = request.user if request.user.is_authenticated else None
            try:
                if tipo == "ENTRADA":
                    registrar_entrada(
                        producto.id,
                        cantidad,
                        observacion,
                        fecha=fecha_completa,
                        usuario=usuario,
                    )
                    messages.success(request, f"Entrada registrada: +{cantidad} u. de '{producto.nombre}'.")
                elif tipo == "SALIDA":
                    registrar_salida(
                        producto.id,
                        cantidad,
                        observacion,
                        fecha=fecha_completa,
                        usuario=usuario,
                    )
                    messages.success(request, f"Salida registrada: -{cantidad} u. de '{producto.nombre}'.")
                elif tipo == "AJUSTE":
                    registrar_ajuste(
                        producto.id,
                        cantidad,
                        observacion,
                        fecha=fecha_completa,
                        usuario=usuario,
                    )
                    messages.success(request, f"Stock de '{producto.nombre}' ajustado a {cantidad} u.")
                return redirect("movimiento_historial")
            except ValidationError as e:
                err_msg = e.message if hasattr(e, "message") else ", ".join(e.messages)
                messages.error(request, err_msg)
                form.add_error(None, err_msg)
    else:
        form = MovimientoUnificadoForm(initial=initial_data)
    return render(request, "inventario/movimiento_form.html", {"form": form})
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
            usuario = request.user if request.user.is_authenticated else None

            try:
                if tipo == "ENTRADA":
                    registrar_entrada(
                        producto.id,
                        cantidad,
                        observacion,
                        fecha=fecha_completa,
                        usuario=usuario,
                    )
                    messages.success(request, f"Entrada registrada: +{cantidad} u. de '{producto.nombre}'.")
                elif tipo == "SALIDA":
                    registrar_salida(
                        producto.id,
                        cantidad,
                        observacion,
                        fecha=fecha_completa,
                        usuario=usuario,
                    )
                    messages.success(request, f"Salida registrada: -{cantidad} u. de '{producto.nombre}'.")
                elif tipo == "AJUSTE":
                    registrar_ajuste(
                        producto.id,
                        cantidad,
                        observacion,
                        fecha=fecha_completa,
                        usuario=usuario,
                    )
                    messages.success(request, f"Stock de '{producto.nombre}' ajustado a {cantidad} u.")

                return redirect("movimiento_historial")

            except ValidationError as e:
                err_msg = e.message if hasattr(e, "message") else ", ".join(e.messages)
                messages.error(request, err_msg)
                form.add_error(None, err_msg)
    else:
        initial_data = {}
        if producto_id_param:
            initial_data["producto"] = producto_id_param
        form = MovimientoUnificadoForm(initial=initial_data)

    return render(request, "inventario/movimiento_form.html", {"form": form})


def movimiento_historial(request):
    tipo_filtro = request.GET.get("tipo", "").strip()
    producto_filtro = request.GET.get("producto", "").strip()

    movimientos = Movimiento.objects.select_related("producto__categoria", "created_by").all()

    if tipo_filtro:
        movimientos = movimientos.filter(tipo=tipo_filtro)
    if producto_filtro:
        movimientos = movimientos.filter(producto_id=producto_filtro)

    productos = Producto.objects.all().order_by("nombre")

    # Paginación (20 movimientos por página)
    paginator = Paginator(movimientos, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventario/movimiento_historial.html",
        {
            "movimientos": page_obj,
            "page_obj": page_obj,
            "productos": productos,
            "tipos": Movimiento.TipoMovimiento.choices,
            "tipo_seleccionado": tipo_filtro,
            "producto_seleccionado": producto_filtro,
        },
    )

@transaction.atomic
def export_csv(request):
    """Export the product list as CSV respecting current filters and ordering."""
    query = request.GET.get("q", "").strip()
    categoria_id = request.GET.get("categoria", "").strip()
    solo_stock_bajo = request.GET.get("stock_bajo") == "1"
    orden = request.GET.get("orden")
    dir_param = request.GET.get("dir", "asc")
    whitelist = {
        "nombre": "nombre",
        "categoria": "categoria__nombre",
        "stock_actual": "stock_actual",
        "stock_minimo": "stock_minimo",
    }
    if orden in whitelist:
        order_field = whitelist[orden]
        if dir_param == "desc":
            order_field = f"-{order_field}"
        productos_qs = Producto.objects.filter(activo=True).select_related("categoria").order_by(order_field)
    else:
        productos_qs = Producto.objects.filter(activo=True).select_related("categoria")
    if query:
        productos_qs = productos_qs.filter(Q(nombre__icontains=query) | Q(descripcion__icontains=query))
    if categoria_id:
        productos_qs = productos_qs.filter(categoria_id=categoria_id)
    if solo_stock_bajo:
        productos_qs = productos_qs.filter(stock_actual__lte=F("stock_minimo"))
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = "attachment; filename=productos.csv"
    writer = csv.writer(response)
    writer.writerow(["ID", "Nombre", "Descripción", "Categoría", "Stock Mínimo", "Stock Actual", "Estado"])
    for p in productos_qs:
        estado = "Sin Stock" if p.stock_actual == 0 else ("Stock Bajo" if p.stock_bajo else "Normal")
        writer.writerow([
            p.id,
            p.nombre,
            p.descripcion,
            p.categoria.nombre if p.categoria else "",
            p.stock_minimo,
            p.stock_actual,
            estado,
        ])
    return response
