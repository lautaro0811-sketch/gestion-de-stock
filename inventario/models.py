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