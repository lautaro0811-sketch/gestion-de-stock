from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=150, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripcion")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos",
        verbose_name="Categoria",
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Precio unitario",
    )
    stock_actual = models.PositiveIntegerField(default=0, verbose_name="Stock actual")
    stock_minimo = models.PositiveIntegerField(default=0, verbose_name="Stock minimo")
    activo = models.BooleanField(default=True, verbose_name="activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock_actual__gte=0),
                name="chk_stock_actual_no_negativo",
            ),
            models.CheckConstraint(
                condition=models.Q(stock_minimo__gte=0),
                name="chk_stock_minimo_no_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock_actual})"

    def clean(self):
        super().clean()
        if self.stock_actual is not None and self.stock_actual < 0:
            raise ValidationError({"stock_actual": "El stock actual no puede ser negativo."})
        if self.stock_minimo is not None and self.stock_minimo < 0:
            raise ValidationError({"stock_minimo": "El stock mínimo no puede ser negativo."})

    @property
    def stock_bajo(self):
        """Indica si el stock actual está en o por debajo del stock mínimo."""
        return self.stock_actual <= self.stock_minimo


class MovimientoQuerySet(models.QuerySet):
    def delete(self):
        raise ValidationError("Los registros de auditoría de movimientos no pueden ser eliminados.")

    def update(self, **kwargs):
        raise ValidationError("Los registros de auditoría de movimientos no pueden ser modificados.")


class Movimiento(models.Model):
    class TipoMovimiento(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"
        AJUSTE = "AJUSTE", "Ajuste"

    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="movimientos",
        verbose_name="Producto",
    )
    tipo = models.CharField(
        max_length=10,
        choices=TipoMovimiento.choices,
        verbose_name="Tipo de Movimiento",
    )
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad",
        help_text="Cantidad de unidades involucradas en el movimiento.",
    )
    stock_anterior = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock anterior",
    )
    stock_posterior = models.PositiveIntegerField(
        default=0,
        verbose_name="Stock posterior",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos",
        verbose_name="Usuario / Creado por",
    )
    fecha = models.DateTimeField(default=timezone.now)
    observacion = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Observación",
    )
    pedido = models.ForeignKey(
        "Pedido",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos",
        verbose_name="Pedido",
    )

    objects = MovimientoQuerySet.as_manager()

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad}) el {self.fecha.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        if self.pk is not None and not self._state.adding:
            if Movimiento.objects.filter(pk=self.pk).exists():
                raise ValidationError("Los movimientos de stock son inmutables y no pueden ser modificados.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Los movimientos de stock son inmutables y no pueden ser eliminados.")


class Cliente(models.Model):
    TIPO_DOC_CHOICES = [
        ("DNI", "DNI"),
        ("CUIT", "CUIT"),
    ]

    nombre = models.CharField(max_length=150, verbose_name="Nombre / Razón social")
    tipo_documento = models.CharField(
        max_length=10,
        choices=TIPO_DOC_CHOICES,
        null=True,
        blank=True,
        verbose_name="Tipo de documento",
    )
    numero_documento = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        verbose_name="Número de documento",
    )
    domicilio = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Domicilio de entrega",
    )
    correo = models.EmailField(blank=True, verbose_name="Correo electrónico")
    telefono = models.CharField(max_length=50, blank=True, verbose_name="Teléfono")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ["nombre"]

    def __str__(self):
        if self.tipo_documento and self.numero_documento:
            return f"{self.nombre} ({self.tipo_documento} {self.numero_documento})"
        return self.nombre

    def clean(self):
        super().clean()
        if self.numero_documento:
            self.numero_documento = "".join(c for c in str(self.numero_documento) if c.isdigit())
        if self.telefono:
            self.telefono = "".join(c for c in str(self.telefono) if c.isdigit())
            if len(self.telefono) < 6:
                raise ValidationError({"telefono": "El teléfono debe contener al menos 6 dígitos."})

        if self.tipo_documento or self.numero_documento:
            if self.tipo_documento == "DNI":
                if not self.numero_documento or len(self.numero_documento) not in (7, 8):
                    raise ValidationError({
                        "numero_documento": "El DNI debe contener 7 u 8 dígitos numéricos."
                    })
            elif self.tipo_documento == "CUIT":
                if not self.numero_documento or len(self.numero_documento) != 11:
                    raise ValidationError({
                        "numero_documento": "El CUIT debe contener exactamente 11 dígitos numéricos."
                    })
            else:
                if not self.tipo_documento:
                    raise ValidationError({
                        "tipo_documento": "Debe seleccionar un tipo de documento."
                    })

    def save(self, *args, **kwargs):
        if self.numero_documento:
            self.numero_documento = "".join(c for c in str(self.numero_documento) if c.isdigit())
        if self.telefono:
            self.telefono = "".join(c for c in str(self.telefono) if c.isdigit())
        super().save(*args, **kwargs)


class Pedido(models.Model):
    class EstadoPedido(models.TextChoices):
        CONFIRMADO = "CONFIRMADO", "Confirmado"
        CANCELADO = "CANCELADO", "Cancelado"

    numero_operacion = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Número de operación",
    )
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name="pedidos",
        verbose_name="Cliente",
    )
    cliente_nombre = models.CharField(max_length=150, blank=True, default="", verbose_name="Nombre del cliente al vender")
    cliente_tipo_documento = models.CharField(max_length=10, blank=True, default="", verbose_name="Tipo de documento al vender")
    cliente_numero_documento = models.CharField(max_length=20, blank=True, default="", verbose_name="Documento del cliente al vender")
    cliente_telefono = models.CharField(max_length=50, blank=True, default="", verbose_name="Teléfono del cliente al vender")
    fecha = models.DateTimeField(
        default=timezone.now,
        verbose_name="Fecha",
    )
    estado = models.CharField(
        max_length=15,
        choices=EstadoPedido.choices,
        default=EstadoPedido.CONFIRMADO,
        verbose_name="Estado",
    )
    observacion = models.TextField(
        blank=True,
        null=True,
        verbose_name="Observación",
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Última actualización")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"Pedido #{self.numero_operacion} - {self.cliente.nombre}"

    @property
    def total(self):
        return sum((item.subtotal for item in self.items.all()), Decimal("0.00"))


class PedidoItem(models.Model):
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name="Pedido",
    )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.PROTECT,
        related_name="pedido_items",
        verbose_name="Producto",
    )
    producto_nombre = models.CharField(max_length=150, blank=True, default="", verbose_name="Nombre del producto al vender")
    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad",
    )
    precio_unitario = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        verbose_name="Precio unitario",
    )

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} (${self.precio_unitario})"

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario


class MovimientoCaja(models.Model):
    class TipoMovimientoCaja(models.TextChoices):
        INGRESO = "INGRESO", "Ingreso"
        EGRESO = "EGRESO", "Egreso"

    fecha = models.DateTimeField(default=timezone.now, verbose_name="Fecha")
    tipo = models.CharField(
        max_length=10,
        choices=TipoMovimientoCaja.choices,
        verbose_name="Tipo",
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
        verbose_name="Monto",
    )
    concepto = models.CharField(
        max_length=255,
        verbose_name="Concepto",
    )
    pedido = models.ForeignKey(
        Pedido,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="movimientos_caja",
        verbose_name="Pedido",
    )

    class Meta:
        verbose_name = "Movimiento de Caja"
        verbose_name_plural = "Movimientos de Caja"
        ordering = ["-fecha", "-id"]

    def __str__(self):
        signo = "+" if self.tipo == self.TipoMovimientoCaja.INGRESO else "-"
        return f"{signo}${self.monto} - {self.concepto} ({self.fecha.strftime('%d/%m/%Y %H:%M')})"

