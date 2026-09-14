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