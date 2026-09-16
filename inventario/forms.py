from django import forms
from django.utils import timezone

from .models import Categoria, Movimiento, Producto


class ProductoBaseForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "categoria", "stock_minimo", "descripcion"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del producto"}),
            "categoria": forms.Select(attrs={"class": "form-control"}),
            "stock_minimo": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción..."}),
        }


class ProductoCrearForm(ProductoBaseForm):
    stock_inicial = forms.IntegerField(
        min_value=0,
        initial=0,
        required=False,
        widget=forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        help_text="Stock de apertura con el que ingresa el producto al sistema (opcional).",
    )


class ProductoEditarForm(ProductoBaseForm):
    pass


# Alias de retrocompatibilidad si fuera necesario
ProductoForm = ProductoCrearForm


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de la categoría"}),
        }


class MovimientoUnificadoForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset=Producto.objects.filter(activo=True).order_by("nombre"),
        empty_label="Seleccione un producto...",
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    fecha = forms.DateField(
        initial=timezone.now().date,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
    )
    tipo = forms.ChoiceField(
        choices=Movimiento.TipoMovimiento.choices,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    cantidad = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(
            attrs={"placeholder": "Cantidad o Stock Real", "class": "form-control"}
        ),
        help_text="Para Ajuste Físico, ingrese el stock real verificado.",
    )
    observacion = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "placeholder": "Observaciones opcionales...",
                "rows": 3,
                "class": "form-control",
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo")
        producto = cleaned_data.get("producto")
        cantidad = cleaned_data.get("cantidad")

        if tipo in [Movimiento.TipoMovimiento.ENTRADA, Movimiento.TipoMovimiento.SALIDA]:
            if cantidad is not None and cantidad <= 0:
                self.add_error(
                    "cantidad",
                    f"Para movimientos de {tipo.lower().capitalize()}, la cantidad debe ser mayor a cero.",
                )

        if tipo == Movimiento.TipoMovimiento.SALIDA and producto and cantidad:
            if cantidad > producto.stock_actual:
                self.add_error(
                    "cantidad",
                    f"Stock insuficiente para '{producto.nombre}'. Hay {producto.stock_actual} u. disponibles y se solicitaron {cantidad} u.",
                )

        if tipo == Movimiento.TipoMovimiento.AJUSTE and producto and cantidad is not None:
            if cantidad == producto.stock_actual:
                self.add_error(
                    "cantidad",
                    f"El stock ingresado ({cantidad}) es idéntico al actual ({producto.stock_actual} u.); no hay ajuste que registrar.",
                )

        return cleaned_data