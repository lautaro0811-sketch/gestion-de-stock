from django import forms
from django.utils import timezone

from .models import Categoria, Movimiento, Producto


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["nombre", "descripcion", "categoria", "stock_actual", "stock_minimo"]
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre del producto"}),
            "descripcion": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Descripción..."}),
            "categoria": forms.Select(attrs={"class": "form-control"}),
            "stock_actual": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
            "stock_minimo": forms.NumberInput(attrs={"class": "form-control", "min": 0}),
        }


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