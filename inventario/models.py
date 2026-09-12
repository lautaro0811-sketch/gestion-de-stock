from django.core.validators import MinValueValidator
from django.db import models


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

    def __str__(self):
        return f"{self.nombre} (Stock: {self.stock_actual})"

    @property
    def stock_bajo(self):
        """Indica si el stock actual está en o por debajo del stock mínimo."""
        return self.stock_actual <= self.stock_minimo

class Movimiento(models.Model):
    class TipoMovimiento(models.TextChoices):
        ENTRADA = "ENTRADA", "Entrada"
        SALIDA = "SALIDA", "Salida"
        AJUSTE = "AJUSTE", "Ajuste"

    producto = models.ForeignKey(
        Producto,
        on_delete= models.PROTECT,
        related_name="movimientos",
        verbose_name="Producto",
    )
    tipo = models.CharField(max_length=10,choices=TipoMovimiento.choices, verbose_name="Tipo de Movimiento",)

    cantidad = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Cantidad",
        help_text="Cantidad de unidades involucradas en el movimiento.",
        )
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha y hora")
    observacion = models.CharField(max_length=255, blank=True, null=True, verbose_name="Observación",)

    class Meta:
        verbose_name = "Movimiento"
        verbose_name_plural = "Movimientos"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad}) el {self.fecha.strftime('%d/%m/%Y %H:%M')}"