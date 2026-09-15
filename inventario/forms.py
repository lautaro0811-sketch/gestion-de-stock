from django import forms
from .models import Categoria, Producto

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ["nombre"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Desinfectantes",
                }
            ),
        }

class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        # Excluimos stock_actual para respetar la regla de negocio
        fields = ["nombre", "categoria", "descripcion", "stock_minimo"]
        widgets = {
            "nombre": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Ej. Lavandina 1L",  
                }
            ),
            "categoria": forms.Select(attrs={"class": "form-control"}),
            "descripcion": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Detalles del producto (opcional)",
                }
            ),
            "stock_minimo": forms.NumberInput(
                attrs={"class": "form-control", "min": "0"}
            ),
        }

class MovimientoCantidadForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset = Producto.objects.filter(activo=True),
        label = "Producto",
        widget=forms.Select(attrs={"class" : "form-control"}),
    )
    cantidad = forms.IntegerField(
        min_value= 1,
        label = "Cantidad",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "1"})
    )
    observacion = forms.CharField(
        required=False,
        label="Observación (opcional)",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Detalle del movimiento (remito, proveedor, motivo, etc.)"
        })
    )

class MovimientoAjusteForm(forms.Form):
    producto = forms.ModelChoiceField(
        queryset = Producto.objects.filter(activo=True),
        label = "Producto",
        widget=forms.Select(attrs={"class" : "form-control"}),
    )
    stock_real = forms.IntegerField(
        min_value = 0,
        label = "Stock",
        widget=forms.NumberInput(attrs={"class": "form-control", "min": "0"})
    )
    observacion = forms.CharField(
        required=False,
        label="Observación (opcional)",
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": "Motivo de ajuste (rotura, pérdida, conteo anual.)"
        })
    )