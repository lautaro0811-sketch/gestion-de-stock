from django.core.exceptions import ValidationError


def validar_documento(tipo_documento, numero_documento):
    if not tipo_documento and not numero_documento:
        return

    if tipo_documento == "DNI":
        if not numero_documento or len(numero_documento) not in (7, 8):
            raise ValidationError({
                "numero_documento": "El DNI debe contener 7 u 8 dígitos numéricos."
            })
    elif tipo_documento == "CUIT":
        if not numero_documento or len(numero_documento) != 11:
            raise ValidationError({
                "numero_documento": "El CUIT debe contener exactamente 11 dígitos numéricos."
            })
    elif not tipo_documento:
        raise ValidationError({
            "tipo_documento": "Debe seleccionar un tipo de documento."
        })
