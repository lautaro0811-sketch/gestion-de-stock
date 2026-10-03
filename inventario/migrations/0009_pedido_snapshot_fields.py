from django.db import migrations, models


def populate_snapshots(apps, schema_editor):
    Pedido = apps.get_model("inventario", "Pedido")
    PedidoItem = apps.get_model("inventario", "PedidoItem")
    database = schema_editor.connection.alias

    for pedido in Pedido.objects.using(database).select_related("cliente").iterator():
        cliente = pedido.cliente
        Pedido.objects.using(database).filter(pk=pedido.pk).update(
            cliente_nombre=cliente.nombre,
            cliente_tipo_documento=cliente.tipo_documento or "",
            cliente_numero_documento=cliente.numero_documento or "",
            cliente_telefono=cliente.telefono or "",
        )

    for item in PedidoItem.objects.using(database).select_related("producto").iterator():
        PedidoItem.objects.using(database).filter(pk=item.pk).update(
            producto_nombre=item.producto.nombre,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("inventario", "0008_producto_precio_unitario_pedido_movimiento_pedido_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedido",
            name="cliente_nombre",
            field=models.CharField(blank=True, default="", max_length=150, verbose_name="Nombre del cliente al vender"),
        ),
        migrations.AddField(
            model_name="pedido",
            name="cliente_tipo_documento",
            field=models.CharField(blank=True, default="", max_length=10, verbose_name="Tipo de documento al vender"),
        ),
        migrations.AddField(
            model_name="pedido",
            name="cliente_numero_documento",
            field=models.CharField(blank=True, default="", max_length=20, verbose_name="Documento del cliente al vender"),
        ),
        migrations.AddField(
            model_name="pedido",
            name="cliente_telefono",
            field=models.CharField(blank=True, default="", max_length=50, verbose_name="Teléfono del cliente al vender"),
        ),
        migrations.AddField(
            model_name="pedidoitem",
            name="producto_nombre",
            field=models.CharField(blank=True, default="", max_length=150, verbose_name="Nombre del producto al vender"),
        ),
        migrations.RunPython(populate_snapshots, migrations.RunPython.noop),
    ]