from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def param_replace(context, **kwargs):
    """Conserva los parámetros GET existentes en la petición,

    actualizando o eliminando los valores pasados como kwargs.
    Ejemplo de uso: <a href="?{% param_replace page=page_obj.next_page_number %}">
    """
    request = context.get("request")
    if not request:
        return ""

    params = request.GET.copy()
    for key, value in kwargs.items():
        if value is not None and value != "":
            params[key] = value
        else:
            params.pop(key, None)
    return params.urlencode()

