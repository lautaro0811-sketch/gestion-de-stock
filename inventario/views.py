import csv
import sqlite3
from datetime import datetime
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.staticfiles import finders
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import connection, transaction
from django.db.models import F, Q, Count, Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from xhtml2pdf import pisa

from .forms import (
    CategoriaForm,
    ClienteForm,
    EgresoCajaForm,
    ItemPedidoFormSet,
    MovimientoUnificadoForm,
    PedidoForm,
    ProductoCrearForm,
    ProductoEditarForm,
)
from .models import Categoria, Cliente, Movimiento, MovimientoCaja, Pedido, PedidoItem, Producto

from .services import (
    cancelar_pedido,
    crear_pedido,
    registrar_ajuste,
    registrar_egreso_caja,
    registrar_entrada,
    registrar_salida,
)


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

    # Annotate each category with count of active products
    categorias = Categoria.objects.annotate(
        productos_activos=Count('productos', filter=Q(productos__activo=True))
    )
    return render(
        request,
        "inventario/categoria_list.html",
        {"categorias": categorias, "form": form},
    )


# --- CLIENTES ---
def cliente_list_crear(request):
    if request.method == "POST":
        form = ClienteForm(request.POST)
        if form.is_valid():
            cliente = form.save()
            messages.success(request, f"Cliente '{cliente.nombre}' registrado con éxito.")
            return redirect("cliente_list")
    else:
        form = ClienteForm()

    clientes = Cliente.objects.filter(activo=True)
    query = request.GET.get("q", "").strip()
    if query:
        filtro = Q(nombre__icontains=query) | Q(numero_documento__icontains=query)
        query_digits = "".join(c for c in query if c.isdigit())
        if query_digits:
            filtro |= Q(numero_documento__icontains=query_digits)
            if query.isdigit():
                filtro |= Q(id=int(query))
        clientes = clientes.filter(filtro)

    paginator = Paginator(clientes, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventario/cliente_list.html",
        {
            "clientes": page_obj,
            "page_obj": page_obj,
            "form": form,
            "query": query,
        },
    )


def cliente_desactivar(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk, activo=True)
    if request.method == "POST":
        cliente.activo = False
        cliente.save(update_fields=["activo"])
        messages.success(request, f"Cliente '{cliente.nombre}' dado de baja correctamente.")
        return redirect("cliente_list")

    return render(request, "inventario/cliente_confirm_delete.html", {"cliente": cliente})



# --- MOVIMIENTOS ---
@transaction.atomic
def movimiento_crear(request):
    """Vista unificada para registrar Entrada, Salida o Ajuste."""
    
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
        # Safely convert the product ID to an integer
        if producto_id_param:
            try:
                producto_id = int(producto_id_param)
                initial_data["producto"] = producto_id
            except ValueError:
                # Invalid ID; ignore and let form validation handle it
                pass
        # Preserve movement type if provided via query string
        tipo_param = request.GET.get("tipo")
        if tipo_param:
            initial_data["tipo"] = tipo_param
        form = MovimientoUnificadoForm(initial=initial_data)

    return render(request, "inventario/movimiento_form.html", {"form": form})


def movimiento_historial(request):
    tipo_filtro = request.GET.get("tipo", "").strip()
    producto_filtro = request.GET.get("producto", "").strip()

    movimientos = Movimiento.objects.select_related("producto__categoria", "created_by", "pedido").all()

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

# --- PEDIDOS DE VENTA ---
def pedido_list(request):
    pedidos = Pedido.objects.select_related("cliente").prefetch_related("items__producto").all()
    query = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "").strip()

    if query:
        pedidos = pedidos.filter(
            Q(numero_operacion__icontains=query)
            | Q(cliente__nombre__icontains=query)
            | Q(cliente__numero_documento__icontains=query)
        )
    if estado:
        pedidos = pedidos.filter(estado=estado)

    paginator = Paginator(pedidos, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventario/pedido_list.html",
        {
            "pedidos": page_obj,
            "page_obj": page_obj,
            "query": query,
            "estado_seleccionado": estado,
            "estados": Pedido.EstadoPedido.choices,
        },
    )


@transaction.atomic
def pedido_crear(request):
    if request.method == "POST":
        form = PedidoForm(request.POST)
        formset = ItemPedidoFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            cliente = form.cleaned_data["cliente"]
            fecha_date = form.cleaned_data["fecha"]
            observacion = form.cleaned_data.get("observacion", "")

            hora_actual = timezone.now().time()
            fecha_completa = timezone.make_aware(
                datetime.combine(fecha_date, hora_actual)
            )
            usuario = request.user if request.user.is_authenticated else None

            # Extraer ítems válidos
            items_data = []
            for item_form in formset:
                if item_form.cleaned_data and not item_form.cleaned_data.get("DELETE", False):
                    producto = item_form.cleaned_data.get("producto")
                    cantidad = item_form.cleaned_data.get("cantidad")
                    if producto and cantidad and cantidad > 0:
                        items_data.append({
                            "producto_id": producto.id,
                            "cantidad": cantidad,
                            "precio_unitario": producto.precio_unitario,
                        })

            if not items_data:
                messages.error(request, "Debe agregar al menos un producto al pedido.")
            else:
                try:
                    pedido = crear_pedido(
                        cliente_id=cliente.id,
                        items_data=items_data,
                        usuario=usuario,
                        fecha=fecha_completa,
                        observacion=observacion,
                    )
                    messages.success(
                        request,
                        f"Pedido #{pedido.numero_operacion} registrado exitosamente para '{cliente.nombre}'."
                    )
                    return redirect("pedido_detalle", pk=pedido.pk)
                except ValidationError as e:
                    err_msg = e.message if hasattr(e, "message") else ", ".join(e.messages)
                    messages.error(request, err_msg)
                    form.add_error(None, err_msg)
    else:
        form = PedidoForm()
        formset = ItemPedidoFormSet()

    productos = list(Producto.objects.filter(activo=True).order_by("nombre"))
    productos_json = [
        {"id": p.id, "nombre": p.nombre, "precio": float(p.precio_unitario), "stock": p.stock_actual}
        for p in productos
    ]

    return render(
        request,
        "inventario/pedido_form.html",
        {
            "form": form,
            "formset": formset,
            "productos": productos,
            "productos_json": productos_json,
        },
    )


def pedido_detalle(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("cliente").prefetch_related(
            "items__producto", "movimientos__producto", "movimientos__created_by"
        ),
        pk=pk,
    )
    return render(
        request,
        "inventario/pedido_detalle.html",
        {"pedido": pedido},
    )


def _pdf_static_link_callback(uri, rel):
    static_prefix = settings.STATIC_URL.strip("/")
    resource_path = uri.lstrip("/")
    if resource_path.startswith(f"{static_prefix}/"):
        resource_path = resource_path[len(static_prefix) + 1:]
        return finders.find(resource_path) or uri
    return uri


def pedido_pdf_view(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("cliente").prefetch_related("items__producto"),
        pk=pk,
    )
    html = render_to_string("inventario/pdf/remito.html", {"pedido": pedido})
    pdf_buffer = BytesIO()
    result = pisa.CreatePDF(
        html,
        dest=pdf_buffer,
        encoding="UTF-8",
        link_callback=_pdf_static_link_callback,
    )
    if result.err:
        return HttpResponse("No se pudo generar el remito.", status=500)

    response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="Remito_{pedido.numero_operacion}.pdf"'
    )
    return response


def descargar_backup(request):
    if connection.vendor != "sqlite":
        return HttpResponse("La descarga de backup solo está disponible para SQLite.", status=501)

    backup_connection = sqlite3.connect(":memory:")
    try:
        connection.ensure_connection()
        connection.connection.backup(backup_connection)
        backup_file = BytesIO(backup_connection.serialize())
    except sqlite3.Error:
        return HttpResponse("No se pudo generar la copia de seguridad.", status=500)
    finally:
        backup_connection.close()

    filename = f"backup_{timezone.localtime():%Y%m%d_%H%M%S}.sqlite3"
    return FileResponse(
        backup_file,
        as_attachment=True,
        filename=filename,
        content_type="application/vnd.sqlite3",
    )


def pedido_cancelar(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == "POST":
        motivo = request.POST.get("motivo", "").strip()
        usuario = request.user if request.user.is_authenticated else None
        try:
            cancelar_pedido(pedido_id=pedido.id, usuario=usuario, motivo=motivo)
            messages.success(
                request,
                f"Pedido #{pedido.numero_operacion} cancelado correctamente. El stock ha sido restituido."
            )
            return redirect("pedido_detalle", pk=pedido.pk)
        except ValidationError as e:
            err_msg = e.message if hasattr(e, "message") else ", ".join(e.messages)
            messages.error(request, err_msg)
            return redirect("pedido_detalle", pk=pedido.pk)

    return render(
        request,
        "inventario/pedido_confirm_cancel.html",
        {"pedido": pedido},
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
    writer.writerow(["ID", "Nombre", "Descripción", "Categoría", "Precio Unitario", "Stock Mínimo", "Stock Actual", "Estado"])
    for p in productos_qs:
        estado = "Sin Stock" if p.stock_actual == 0 else ("Stock Bajo" if p.stock_bajo else "Normal")
        writer.writerow([
            p.id,
            p.nombre,
            p.descripcion,
            p.categoria.nombre if p.categoria else "",
            f"${p.precio_unitario:.2f}",
            p.stock_minimo,
            p.stock_actual,
            estado,
        ])
    return response


# --- CAJA ---
def caja_dashboard(request):
    """Dashboard de caja con saldo calculado dinámicamente."""
    from decimal import Decimal

    agregados = MovimientoCaja.objects.aggregate(
        total_ingresos=Sum("monto", filter=Q(tipo="INGRESO")),
        total_egresos=Sum("monto", filter=Q(tipo="EGRESO")),
    )

    total_ingresos = agregados["total_ingresos"] or Decimal("0.00")
    total_egresos = agregados["total_egresos"] or Decimal("0.00")
    saldo = total_ingresos - total_egresos

    movimientos = MovimientoCaja.objects.select_related("pedido").all()

    paginator = Paginator(movimientos, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request,
        "inventario/caja_dashboard.html",
        {
            "total_ingresos": total_ingresos,
            "total_egresos": total_egresos,
            "saldo": saldo,
            "movimientos": page_obj,
            "page_obj": page_obj,
        },
    )


def caja_egreso_crear(request):
    """Registra un egreso manual de caja."""
    if request.method == "POST":
        form = EgresoCajaForm(request.POST)
        if form.is_valid():
            monto = form.cleaned_data["monto"]
            concepto = form.cleaned_data["concepto"]
            try:
                registrar_egreso_caja(monto=monto, concepto=concepto)
                messages.success(request, f"Egreso de ${monto} registrado correctamente: {concepto}")
                return redirect("caja_dashboard")
            except ValidationError as e:
                err_msg = e.message if hasattr(e, "message") else ", ".join(e.messages)
                messages.error(request, err_msg)
    else:
        form = EgresoCajaForm()

    return render(
        request,
        "inventario/caja_egreso_form.html",
        {"form": form},
    )
