from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import Movimiento, Producto


@transaction.atomic
def registrar_entrada(
    producto_id: int,
    cantidad: int,
    observacion: str = "",
    fecha=None,
    usuario=None,
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