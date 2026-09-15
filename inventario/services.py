from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Movimiento, Producto


@transaction.atomic
def registrar_entrada(producto_id: int, cantidad: int, observacion: str = "", fecha=None) -> Movimiento:
    """Registra un ingreso de stock incrementando el saldo actual."""
    if cantidad <= 0:
        raise ValidationError("La cantidad a ingresar debe ser mayor a cero.")

    producto = Producto.objects.select_for_update().get(pk=producto_id)

    # 1. Registrar movimiento histórico
    movimiento = Movimiento.objects.create(
        producto=producto,
        tipo=Movimiento.TipoMovimiento.ENTRADA,
        cantidad=cantidad,
        observacion=observacion,
        fecha=fecha or timezone.now(),
    )

    # 2. Actualizar stock actual del producto
    producto.stock_actual += cantidad
    producto.save(update_fields=["stock_actual", "fecha_actualizacion"])

    return movimiento


@transaction.atomic
def registrar_salida(producto_id: int, cantidad: int, observacion: str = "", fecha=None) -> Movimiento:
    """Registra una salida de stock previa validación de existencia suficiente."""
    if cantidad <= 0:
        raise ValidationError("La cantidad a egresar debe ser mayor a cero.")

    producto = Producto.objects.select_for_update().get(pk=producto_id)

    if producto.stock_actual < cantidad:
        raise ValidationError(
            f"Stock insuficiente para '{producto.nombre}'. "
            f"Disponible: {producto.stock_actual}, Solicitado: {cantidad}."
        )

    # 1. Registrar movimiento histórico
    movimiento = Movimiento.objects.create(
        producto=producto,
        tipo=Movimiento.TipoMovimiento.SALIDA,
        cantidad=cantidad,
        observacion=observacion,
        fecha=fecha or timezone.now(),
    )

    # 2. Actualizar stock actual del producto
    producto.stock_actual -= cantidad
    producto.save(update_fields=["stock_actual", "fecha_actualizacion"])

    return movimiento


@transaction.atomic
def registrar_ajuste(producto_id: int, stock_real: int, observacion: str = "",fecha=None) -> Movimiento:
    """Ajusta el stock al valor real verificado en conteo físico."""
    if stock_real < 0:
        raise ValidationError("El stock real contado no puede ser negativo.")

    producto = Producto.objects.select_for_update().get(pk=producto_id)

    if stock_real == producto.stock_actual:
        raise ValidationError("El stock ingresado es idéntico al stock actual; no hay ajuste que registrar.")

    # Calculamos la diferencia absoluta para guardarla en el movimiento
    diferencia = abs(stock_real - producto.stock_actual)
    direccion = "incremento" if stock_real > producto.stock_actual else "decremento"

    detalle_ajuste = f"Ajuste físico ({direccion} de {diferencia} u.). Anterior: {producto.stock_actual}, Real: {stock_real}."
    obs_final = f"{detalle_ajuste} {observacion}".strip()

    # 1. Registrar movimiento histórico
    movimiento = Movimiento.objects.create(
        producto=producto,
        tipo=Movimiento.TipoMovimiento.AJUSTE,
        cantidad=diferencia,
        observacion=obs_final,
        fecha=fecha or timezone.now(),
    )

    # 2. Asignar el nuevo valor real de stock
    producto.stock_actual = stock_real
    producto.save(update_fields=["stock_actual", "fecha_actualizacion"])

    return movimiento