from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Cliente, Movimiento, Pedido, PedidoItem, Producto


@transaction.atomic
def registrar_entrada(
    producto_id: int,
    cantidad: int,
    observacion: str = "",
    fecha=None,
    usuario=None,
    pedido_id: int = None,
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


@transaction.atomic
def crear_pedido(
    cliente_id: int,
    items_data: list,
    usuario=None,
    fecha=None,
    observacion: str = "",
) -> Pedido:
    """Crea un pedido de venta generando número correlativo y descontando stock."""
    if not items_data:
        raise ValidationError("El pedido debe contener al menos un ítem.")

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

    pedido = Pedido.objects.create(
        numero_operacion=numero_operacion,
        cliente=cliente,
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

    return pedido


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

    return pedido