from django import forms
from django.utils import timezone

from .models import Categoria, Cliente, Movimiento, Producto


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


class ClienteForm(forms.ModelForm):
    tipo_documento = forms.ChoiceField(
        choices=[("", "Seleccionar..."), ("DNI", "DNI"), ("CUIT", "CUIT")],
        required=True,
        label="Tipo de documento",
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    class Meta:
        model = Cliente
        fields = [
            "nombre",
            "tipo_documento",
            "numero_documento",
            "domicilio",
            "correo",
            "telefono",
        ]
        labels = {
            "nombre": "Nombre / Razón social",
            "tipo_documento": "Tipo de documento",
            "numero_documento": "CUIT / DNI",
            "domicilio": "Domicilio de entrega",
            "correo": "Correo electrónico",
            "telefono": "Teléfono",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre o razón social"}),
            "tipo_documento": forms.Select(attrs={"class": "form-control"}),
            "numero_documento": forms.TextInput(attrs={"class": "form-control", "placeholder": "Número de documento o CUIT"}),
            "domicilio": forms.TextInput(attrs={"class": "form-control", "placeholder": "Domicilio de entrega"}),
            "correo": forms.EmailInput(attrs={"class": "form-control", "placeholder": "ejemplo@correo.com"}),
            "telefono": forms.TextInput(attrs={"class": "form-control", "placeholder": "Teléfono de contacto"}),
        }

    def clean_numero_documento(self):
        num = self.cleaned_data.get("numero_documento", "")
        num_limpio = "".join(c for c in str(num) if c.isdigit())
        if not num_limpio:
            raise forms.ValidationError("El número de documento debe contener al menos un dígito.")
        return num_limpio

    def clean_telefono(self):
        tel = self.cleaned_data.get("telefono", "")
        if not tel:
            return ""
        tel_limpio = "".join(c for c in str(tel) if c.isdigit())
        if len(tel_limpio) < 6:
            raise forms.ValidationError("El teléfono debe contener al menos 6 dígitos.")
        return tel_limpio

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get("tipo_documento")
        numero = cleaned_data.get("numero_documento")

        if tipo and numero:
            if tipo == "DNI":
                if len(numero) not in (7, 8):
                    self.add_error("numero_documento", "El DNI debe contener 7 u 8 dígitos numéricos.")
            elif tipo == "CUIT":
                if len(numero) != 11:
                    self.add_error("numero_documento", "El CUIT debe contener exactamente 11 dígitos numéricos.")
        return cleaned_data



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