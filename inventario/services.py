from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    Cliente,
    Movimiento,
    MovimientoCaja,
    OrdenCompra,
    OrdenCompraItem,
    Pedido,
    PedidoItem,
    Producto,
    Proveedor,
)


@transaction.atomic
def registrar_entrada(
    producto_id: int,
    cantidad: int,
    observacion: str = "",
    fecha=None,
    usuario=None,
    pedido_id: int = None,
    orden_compra_id: int = None,
) -> Movimiento:
    """Registra un ingreso de stock incrementando el saldo actual."""
    if cantidad <= 0:
        raise ValidationError("La cantidad a ingresar debe ser mayor a cero.")

    producto = Producto.objects.select_for_update().get(pk=producto_id)

    stock_anterior = producto.stock_actual
    stock_posterior = stock_anterior + cantidad

    # 1. Registrar movimiento histórico con cálculo atómico y auditoría
    movimiento = Movimiento.objects.create(
        producto=producto,
        tipo=Movimiento.TipoMovimiento.ENTRADA,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_posterior=stock_posterior,
        created_by=usuario,
        observacion=observacion,
        fecha=fecha or timezone.now(),
        pedido_id=pedido_id,
        orden_compra_id=orden_compra_id,
    )

    # 2. Actualizar stock actual del producto
    producto.stock_actual = stock_posterior
    producto.save(update_fields=["stock_actual", "fecha_actualizacion"])

    return movimiento


@transaction.atomic
def registrar_salida(
    producto_id: int,
    cantidad: int,
    observacion: str = "",
    fecha=None,
    usuario=None,
    pedido_id: int = None,
) -> Movimiento:
    """Registra una salida de stock previa validación de existencia suficiente."""
    if cantidad <= 0:
        raise ValidationError("La cantidad a egresar debe ser mayor a cero.")

    producto = Producto.objects.select_for_update().get(pk=producto_id)

    if producto.stock_actual < cantidad:
        raise ValidationError(
            f"Stock insuficiente para '{producto.nombre}'. "
            f"Disponible: {producto.stock_actual}, Solicitado: {cantidad}."
        )

    stock_anterior = producto.stock_actual
    stock_posterior = stock_anterior - cantidad

    # 1. Registrar movimiento histórico con cálculo atómico y auditoría
    movimiento = Movimiento.objects.create(
        producto=producto,
        tipo=Movimiento.TipoMovimiento.SALIDA,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_posterior=stock_posterior,
        created_by=usuario,
        observacion=observacion,
        fecha=fecha or timezone.now(),
        pedido_id=pedido_id,
    )

    # 2. Actualizar stock actual del producto
    producto.stock_actual = stock_posterior
    producto.save(update_fields=["stock_actual", "fecha_actualizacion"])

    return movimiento


@transaction.atomic
def registrar_ajuste(
    producto_id: int,
    stock_real: int,
    observacion: str = "",
    fecha=None,
    usuario=None,
) -> Movimiento:
    """Ajusta el stock al valor real verificado en conteo físico."""
    if stock_real < 0:
        raise ValidationError("El stock real contado no puede ser negativo.")

    producto = Producto.objects.select_for_update().get(pk=producto_id)

    if stock_real == producto.stock_actual:
        raise ValidationError("El stock ingresado es idéntico al stock actual; no hay ajuste que registrar.")

    stock_anterior = producto.stock_actual
    stock_posterior = stock_real

    # Calculamos la diferencia absoluta para guardarla en el movimiento
    diferencia = abs(stock_real - stock_anterior)
    direccion = "incremento" if stock_real > stock_anterior else "decremento"

    detalle_ajuste = f"Ajuste físico ({direccion} de {diferencia} u.). Anterior: {stock_anterior}, Real: {stock_real}."
    obs_final = f"{detalle_ajuste} {observacion}".strip()

    # 1. Registrar movimiento histórico con cálculo atómico y auditoría
    movimiento = Movimiento.objects.create(
        producto=producto,
        tipo=Movimiento.TipoMovimiento.AJUSTE,
        cantidad=diferencia,
        stock_anterior=stock_anterior,
        stock_posterior=stock_posterior,
        created_by=usuario,
        observacion=obs_final,
        fecha=fecha or timezone.now(),
    )

    # 2. Asignar el nuevo valor real de stock
    producto.stock_actual = stock_posterior
    producto.save(update_fields=["stock_actual", "fecha_actualizacion"])

    return movimiento


def registrar_ingreso_caja(
    monto,
    concepto: str,
    pedido=None,
) -> MovimientoCaja:
    """Registra un ingreso de dinero en la caja."""
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValidationError("El monto del ingreso debe ser mayor a cero.")

    return MovimientoCaja.objects.create(
        tipo=MovimientoCaja.TipoMovimientoCaja.INGRESO,
        monto=monto,
        concepto=concepto,
        pedido=pedido,
    )


def registrar_egreso_caja(
    monto,
    concepto: str,
    pedido=None,
    orden_compra=None,
) -> MovimientoCaja:
    """Registra un egreso de dinero de la caja."""
    monto = Decimal(str(monto))
    if monto <= 0:
        raise ValidationError("El monto del egreso debe ser mayor a cero.")

    return MovimientoCaja.objects.create(
        tipo=MovimientoCaja.TipoMovimientoCaja.EGRESO,
        monto=monto,
        concepto=concepto,
        pedido=pedido,
        orden_compra=orden_compra,
    )


@transaction.atomic
def crear_pedido(
    cliente_id: int | None,
    items_data: list,
    usuario=None,
    fecha=None,
    observacion: str = "",
    nombre_comprador: str = "",
) -> Pedido:
    """Crea un pedido de venta generando número correlativo y descontando stock."""
    if not items_data:
        raise ValidationError("El pedido debe contener al menos un ítem.")

    cliente = None
    if cliente_id is not None:
        try:
            cliente = Cliente.objects.get(pk=cliente_id, activo=True)
        except Cliente.DoesNotExist:
            raise ValidationError("El cliente seleccionado no existe o no está activo.")

    fecha_pedido = fecha or timezone.now()
    anio = fecha_pedido.year
    prefix = f"{anio}-"

    ultimo = (
        Pedido.objects.filter(numero_operacion__startswith=prefix)
        .select_for_update()
        .order_by("-numero_operacion")
        .first()
    )
    if ultimo:
        try:
            ultimo_seq = int(ultimo.numero_operacion.split("-")[1])
            siguiente_seq = ultimo_seq + 1
        except (IndexError, ValueError):
            siguiente_seq = Pedido.objects.filter(numero_operacion__startswith=prefix).count() + 1
    else:
        siguiente_seq = 1

    numero_operacion = f"{anio}-{siguiente_seq:04d}"
    while Pedido.objects.filter(numero_operacion=numero_operacion).exists():
        siguiente_seq += 1
        numero_operacion = f"{anio}-{siguiente_seq:04d}"

    if cliente:
        cliente_nombre = cliente.nombre
        cliente_tipo_documento = cliente.tipo_documento or ""
        cliente_numero_documento = cliente.numero_documento or ""
        cliente_telefono = cliente.telefono
    else:
        cliente_nombre = nombre_comprador.strip() or "Consumidor Final"
        cliente_tipo_documento = ""
        cliente_numero_documento = ""
        cliente_telefono = ""

    pedido = Pedido.objects.create(
        numero_operacion=numero_operacion,
        cliente=cliente,
        cliente_nombre=cliente_nombre,
        cliente_tipo_documento=cliente_tipo_documento,
        cliente_numero_documento=cliente_numero_documento,
        cliente_telefono=cliente_telefono,
        fecha=fecha_pedido,
        estado=Pedido.EstadoPedido.CONFIRMADO,
        observacion=observacion,
    )

    for item in items_data:
        producto_id = item.get("producto_id")
        cantidad = item.get("cantidad")

        if not producto_id or cantidad is None:
            raise ValidationError("Cada ítem debe tener un producto y una cantidad válida.")

        try:
            cantidad = int(cantidad)
        except (ValueError, TypeError):
            raise ValidationError("La cantidad debe ser un número entero.")

        if cantidad <= 0:
            raise ValidationError("La cantidad de cada ítem debe ser mayor a cero.")

        try:
            producto = Producto.objects.get(pk=producto_id, activo=True)
        except Producto.DoesNotExist:
            raise ValidationError(f"El producto con ID {producto_id} no existe o no está activo.")

        # Congelar precio unitario del catálogo
        precio_unitario = item.get("precio_unitario")
        if precio_unitario is None:
            precio_unitario = producto.precio_unitario
        else:
            precio_unitario = Decimal(str(precio_unitario))

        PedidoItem.objects.create(
            pedido=pedido,
            producto=producto,
            producto_nombre=producto.nombre,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
        )

        # Descontar stock mediante registrar_salida
        registrar_salida(
            producto_id=producto.id,
            cantidad=cantidad,
            observacion=f"Venta en Pedido #{pedido.numero_operacion}",
            fecha=fecha_pedido,
            usuario=usuario,
            pedido_id=pedido.id,
        )

    # Registrar ingreso en caja por el total del pedido
    total_pedido = sum(
        (item.cantidad * item.precio_unitario for item in pedido.items.all()),
        Decimal("0.00"),
    )
    registrar_ingreso_caja(
        monto=total_pedido,
        concepto=f"Venta - Pedido #{pedido.numero_operacion}",
        pedido=pedido,
    )

    return pedido


@transaction.atomic
def crear_orden_compra(
    proveedor_id: int,
    items_data: list,
    observacion: str = "",
    fecha=None,
) -> OrdenCompra:
    """Crea una orden pendiente sin modificar el stock de los productos."""
    if not items_data:
        raise ValidationError("La orden de compra debe contener al menos un ítem.")

    try:
        proveedor = Proveedor.objects.get(pk=proveedor_id, activo=True)
    except Proveedor.DoesNotExist:
        raise ValidationError("El proveedor seleccionado no existe o no está activo.")

    fecha_orden = fecha or timezone.now()
    prefijo = f"OC-{fecha_orden.year}-"
    ordenes_anuales = OrdenCompra.objects.filter(numero_operacion__startswith=prefijo)
    ultima = ordenes_anuales.select_for_update().order_by("-numero_operacion").first()

    if ultima:
        try:
            siguiente = int(ultima.numero_operacion.rsplit("-", 1)[1]) + 1
        except (IndexError, ValueError):
            siguiente = ordenes_anuales.count() + 1
    else:
        siguiente = 1

    numero_operacion = f"{prefijo}{siguiente:04d}"
    while OrdenCompra.objects.filter(numero_operacion=numero_operacion).exists():
        siguiente += 1
        numero_operacion = f"{prefijo}{siguiente:04d}"

    orden = OrdenCompra.objects.create(
        numero_operacion=numero_operacion,
        proveedor=proveedor,
        fecha=fecha_orden,
        estado=OrdenCompra.EstadoOrdenCompra.PENDIENTE,
        observacion=observacion,
    )

    for item in items_data:
        producto_id = item.get("producto_id")
        cantidad = item.get("cantidad")
        if not producto_id or cantidad is None:
            raise ValidationError("Cada ítem debe tener un producto y una cantidad válida.")

        try:
            cantidad = int(cantidad)
        except (ValueError, TypeError):
            raise ValidationError("La cantidad debe ser un número entero.")
        if cantidad <= 0:
            raise ValidationError("La cantidad de cada ítem debe ser mayor a cero.")

        try:
            producto = Producto.objects.get(pk=producto_id, activo=True)
        except Producto.DoesNotExist:
            raise ValidationError(f"El producto con ID {producto_id} no existe o no está activo.")

        precio = item.get("precio_unitario_compra")
        if precio is None:
            raise ValidationError("Cada ítem debe incluir un precio unitario de compra.")
        try:
            precio = Decimal(str(precio))
        except (ValueError, TypeError, ArithmeticError):
            raise ValidationError("El precio unitario de compra debe ser un número válido.")
        if not precio.is_finite() or precio < 0:
            raise ValidationError("El precio unitario de compra no puede ser negativo.")

        OrdenCompraItem.objects.create(
            orden_compra=orden,
            producto=producto,
            producto_nombre=producto.nombre,
            cantidad=cantidad,
            precio_unitario_compra=precio,
        )

    return orden


@transaction.atomic
def recibir_mercaderia(
    orden_compra_id: int,
    usuario=None,
    fecha=None,
) -> OrdenCompra:
    """Recibe todos los artículos pendientes e incrementa el stock en una transacción."""
    orden = OrdenCompra.objects.select_for_update().get(pk=orden_compra_id)
    if orden.estado != OrdenCompra.EstadoOrdenCompra.PENDIENTE:
        raise ValidationError("Solo se puede recibir una orden de compra pendiente.")

    items = list(orden.items.select_related("producto").all())
    for item in items:
        registrar_entrada(
            producto_id=item.producto_id,
            cantidad=item.cantidad,
            observacion=f"Recepción de Orden de Compra #{orden.numero_operacion}",
            fecha=fecha or timezone.now(),
            usuario=usuario,
            orden_compra_id=orden.id,
        )

    total_orden = sum(
        (item.cantidad * item.precio_unitario_compra for item in items),
        Decimal("0.00"),
    )
    if total_orden > 0:
        registrar_egreso_caja(
            monto=total_orden,
            concepto=f"Compra - Orden de Compra #{orden.numero_operacion}",
            orden_compra=orden,
        )

    orden.estado = OrdenCompra.EstadoOrdenCompra.RECIBIDA
    orden.save(update_fields=["estado", "fecha_actualizacion"])
    return orden


@transaction.atomic
def cancelar_orden_compra(orden_compra_id: int) -> OrdenCompra:
    """Cancela una orden pendiente sin generar movimientos de stock."""
    orden = OrdenCompra.objects.select_for_update().get(pk=orden_compra_id)
    if orden.estado != OrdenCompra.EstadoOrdenCompra.PENDIENTE:
        raise ValidationError("Solo se puede cancelar una orden de compra pendiente.")

    orden.estado = OrdenCompra.EstadoOrdenCompra.CANCELADA
    orden.save(update_fields=["estado", "fecha_actualizacion"])
    return orden


@transaction.atomic
def cancelar_pedido(
    pedido_id: int,
    usuario=None,
    motivo: str = "",
) -> Pedido:
    """Cancela un pedido confirmado y devuelve el stock mediante movimientos compensatorios de entrada."""
    pedido = Pedido.objects.select_for_update().get(pk=pedido_id)

    if pedido.estado == Pedido.EstadoPedido.CANCELADO:
        raise ValidationError("El pedido ya se encuentra cancelado.")

    pedido.estado = Pedido.EstadoPedido.CANCELADO
    if motivo:
        pedido.observacion = f"{pedido.observacion or ''}\n[Cancelación]: {motivo}".strip()
    pedido.save(update_fields=["estado", "observacion", "fecha_actualizacion"])

    for item in pedido.items.select_related("producto").all():
        registrar_entrada(
            producto_id=item.producto.id,
            cantidad=item.cantidad,
            observacion=f"Compensación por cancelación de Pedido #{pedido.numero_operacion}",
            usuario=usuario,
            pedido_id=pedido.id,
        )

    # Registrar egreso compensatorio en caja
    total_pedido = sum(
        (item.cantidad * item.precio_unitario
         for item in pedido.items.select_related("producto").all()),
        Decimal("0.00"),
    )
    registrar_egreso_caja(
        monto=total_pedido,
        concepto=f"Cancelación - Pedido #{pedido.numero_operacion}",
        pedido=pedido,
    )

    return pedido