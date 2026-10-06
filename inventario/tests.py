import datetime
import sqlite3
from decimal import Decimal

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.db.models.query import QuerySet
from django.template import Context, Template
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, TransactionTestCase
from django.urls import reverse
from django.utils import timezone

from inventario.admin import MovimientoAdmin
from inventario.forms import (
    CategoriaForm,
    ClienteForm,
    EgresoCajaForm,
    ItemPedidoFormSet,
    MovimientoUnificadoForm,
    PedidoForm,
    PedidoItemFormSet,
    ProductoCrearForm,
    ProductoEditarForm,
    ProveedorForm,
)
from inventario.models import (
    Categoria,
    Cliente,
    Movimiento,
    MovimientoCaja,
    OrdenCompra,
    Pedido,
    PedidoItem,
    Producto,
    Proveedor,
)
from inventario.services import (
    cancelar_orden_compra,
    cancelar_pedido,
    crear_orden_compra,
    crear_pedido,
    registrar_ajuste,
    registrar_entrada,
    registrar_salida,
    recibir_mercaderia,
)


class StockBajoFExpressionTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Herramientas")
        # Producto con stock actual menor al mínimo (stock bajo)
        self.p1 = Producto.objects.create(
            nombre="Destornillador", categoria=self.cat, stock_actual=2, stock_minimo=5
        )
        # Producto con stock actual igual al mínimo (stock bajo)
        self.p2 = Producto.objects.create(
            nombre="Martillo", categoria=self.cat, stock_actual=5, stock_minimo=5
        )
        # Producto con stock actual mayor al mínimo (stock normal)
        self.p3 = Producto.objects.create(
            nombre="Taladro", categoria=self.cat, stock_actual=10, stock_minimo=5
        )
        # Producto inactivo con stock bajo (no debe aparecer)
        self.p4 = Producto.objects.create(
            nombre="Sierra Vieja", categoria=self.cat, stock_actual=1, stock_minimo=5, activo=False
        )

    def test_filtro_stock_bajo_a_nivel_sql(self):
        url = reverse("producto_list")
        response = self.client.get(url, {"stock_bajo": "1"})

        self.assertEqual(response.status_code, 200)
        productos_en_contexto = response.context["productos"]

        # Verificar que la colección base del paginador es un QuerySet (filtrado a nivel SQL)
        self.assertTrue(isinstance(productos_en_contexto.paginator.object_list, QuerySet))

        # Comprobar los productos presentes
        nombres = [p.nombre for p in productos_en_contexto]
        self.assertIn("Destornillador", nombres)
        self.assertIn("Martillo", nombres)
        self.assertNotIn("Taladro", nombres)
        self.assertNotIn("Sierra Vieja", nombres)


class ProductoListPaginacionTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Ferretería")
        # Creamos 25 productos
        for i in range(1, 26):
            Producto.objects.create(
                nombre=f"Item {i:02d}",
                categoria=self.cat,
                stock_actual=10,
                stock_minimo=2,
            )

    def test_paginacion_primera_pagina_15_elementos(self):
        response = self.client.get(reverse("producto_list"))
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]

        self.assertEqual(len(page_obj), 15)
        self.assertEqual(page_obj.paginator.count, 25)
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())
        self.assertFalse(page_obj.has_previous())

    def test_paginacion_segunda_pagina_10_elementos(self):
        response = self.client.get(reverse("producto_list"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]

        self.assertEqual(len(page_obj), 10)
        self.assertFalse(page_obj.has_next())
        self.assertTrue(page_obj.has_previous())

    def test_paginacion_pagina_invalida_retorna_primera(self):
        response = self.client.get(reverse("producto_list"), {"page": "invalido"})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.number, 1)

    def test_paginacion_pagina_fuera_de_rango_retorna_ultima(self):
        response = self.client.get(reverse("producto_list"), {"page": 999})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.number, 2)

    def test_paginacion_html_renderiza_links_con_filtros(self):
        response = self.client.get(reverse("producto_list"), {"q": "Item", "page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Página 1 de 2")
        self.assertContains(response, "page=2")
        self.assertContains(response, "q=Item")


class MovimientoHistorialPaginacionTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="General")
        self.producto = Producto.objects.create(
            nombre="Producto Alpha",
            categoria=self.cat,
            stock_actual=0,
            stock_minimo=5,
        )
        # Creamos 25 movimientos (25 entradas)
        for i in range(1, 26):
            registrar_entrada(
                producto_id=self.producto.id,
                cantidad=1,
                observacion=f"Movimiento test {i}",
            )

    def test_paginacion_primera_pagina_20_elementos(self):
        response = self.client.get(reverse("movimiento_historial"))
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]

        self.assertEqual(len(page_obj), 20)
        self.assertEqual(page_obj.paginator.count, 25)
        self.assertEqual(page_obj.paginator.num_pages, 2)
        self.assertTrue(page_obj.has_next())

    def test_paginacion_segunda_pagina_5_elementos(self):
        response = self.client.get(reverse("movimiento_historial"), {"page": 2})
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]

        self.assertEqual(len(page_obj), 5)
        self.assertFalse(page_obj.has_next())

    def test_paginacion_html_renderiza_links_con_filtros_movimientos(self):
        response = self.client.get(reverse("movimiento_historial"), {"tipo": "ENTRADA", "page": 1})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Página 1 de 2")
        self.assertContains(response, "page=2")
        self.assertContains(response, "tipo=ENTRADA")



class TemplateTagParamReplaceTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_param_replace_preserva_y_actualiza(self):
        request = self.factory.get("/productos/?q=tornillo&categoria=1&stock_bajo=1")
        template_str = (
            "{% load inventario_tags %}"
            "?{% param_replace page=2 %}"
        )
        t = Template(template_str)
        rendered = t.render(Context({"request": request}))

        self.assertIn("page=2", rendered)
        self.assertIn("q=tornillo", rendered)
        self.assertIn("categoria=1", rendered)
        self.assertIn("stock_bajo=1", rendered)

    def test_param_replace_elimina_parametro_vacio(self):
        request = self.factory.get("/productos/?q=tornillo&categoria=1")
        template_str = (
            "{% load inventario_tags %}"
            "?{% param_replace q='' page=1 %}"
        )
        t = Template(template_str)
        rendered = t.render(Context({"request": request}))

        self.assertIn("page=1", rendered)
        self.assertIn("categoria=1", rendered)
        self.assertNotIn("q=", rendered)


class AuditoriaServicesStockTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="auditor", password="password123")
        self.cat = Categoria.objects.create(nombre="Electricidad")
        self.producto = Producto.objects.create(
            nombre="Cable 2.5mm",
            categoria=self.cat,
            stock_actual=10,
            stock_minimo=5,
        )

    def test_registrar_entrada_calcula_stock_y_created_by(self):
        m = registrar_entrada(
            producto_id=self.producto.id,
            cantidad=15,
            observacion="Compra mayorista",
            usuario=self.user,
        )
        self.assertEqual(m.stock_anterior, 10)
        self.assertEqual(m.stock_posterior, 25)
        self.assertEqual(m.created_by, self.user)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 25)

    def test_registrar_salida_calcula_stock_y_created_by(self):
        m = registrar_salida(
            producto_id=self.producto.id,
            cantidad=4,
            observacion="Venta mostrador",
            usuario=self.user,
        )
        self.assertEqual(m.stock_anterior, 10)
        self.assertEqual(m.stock_posterior, 6)
        self.assertEqual(m.created_by, self.user)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 6)

    def test_registrar_ajuste_calcula_stock_y_created_by(self):
        m = registrar_ajuste(
            producto_id=self.producto.id,
            stock_real=18,
            observacion="Conteo mensual",
            usuario=self.user,
        )
        self.assertEqual(m.stock_anterior, 10)
        self.assertEqual(m.stock_posterior, 18)
        self.assertEqual(m.cantidad, 8)
        self.assertEqual(m.created_by, self.user)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 18)


class MovimientoInmutabilidadTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Herramientas")
        self.producto = Producto.objects.create(
            nombre="Taladro Percutor",
            categoria=self.cat,
            stock_actual=10,
            stock_minimo=2,
        )
        self.movimiento = registrar_entrada(self.producto.id, 5, observacion="Ingreso inicial")

    def test_movimiento_no_se_puede_modificar_con_save(self):
        self.movimiento.observacion = "Texto editado"
        with self.assertRaises(ValidationError) as ctx:
            self.movimiento.save()
        self.assertIn("inmutables", str(ctx.exception))

    def test_movimiento_no_se_puede_eliminar_con_delete(self):
        with self.assertRaises(ValidationError) as ctx:
            self.movimiento.delete()
        self.assertIn("inmutables", str(ctx.exception))

    def test_movimiento_queryset_update_bloqueado(self):
        with self.assertRaises(ValidationError) as ctx:
            Movimiento.objects.filter(pk=self.movimiento.pk).update(observacion="Hack")
        self.assertIn("no pueden ser modificados", str(ctx.exception))

    def test_movimiento_queryset_delete_bloqueado(self):
        with self.assertRaises(ValidationError) as ctx:
            Movimiento.objects.filter(pk=self.movimiento.pk).delete()
        self.assertIn("no pueden ser eliminados", str(ctx.exception))


class MovimientoAdminBlindajeTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        User = get_user_model()
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpassword"
        )
        self.site = admin.site
        self.model_admin = MovimientoAdmin(Movimiento, self.site)

    def test_permisos_y_acciones_bloqueadas(self):
        request = self.factory.get("/admin/inventario/movimiento/")
        request.user = self.admin_user

        self.assertFalse(self.model_admin.has_add_permission(request))
        self.assertFalse(self.model_admin.has_change_permission(request))
        self.assertFalse(self.model_admin.has_delete_permission(request))
        self.assertIsNone(self.model_admin.actions)


class MovimientoViewsAuditoriaTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="operador", password="operadorpass123")
        self.cat = Categoria.objects.create(nombre="Ferretería")
        self.producto = Producto.objects.create(
            nombre="Clavos 2 pulgadas",
            categoria=self.cat,
            stock_actual=5,
            stock_minimo=2,
        )

    def test_movimiento_crear_asocia_usuario_autenticado(self):
        self.client.login(username="operador", password="operadorpass123")
        url = reverse("movimiento_crear")
        data = {
            "producto": self.producto.id,
            "tipo": "ENTRADA",
            "cantidad": 12,
            "fecha": "2026-09-16",
            "observacion": "Ingreso por recepción de mercadería",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        movimiento = Movimiento.objects.filter(producto=self.producto).latest("id")
        self.assertEqual(movimiento.created_by, self.user)
        self.assertEqual(movimiento.stock_anterior, 5)
        self.assertEqual(movimiento.stock_posterior, 17)

    def test_producto_crear_stock_inicial_asocia_usuario_autenticado(self):
        self.client.login(username="operador", password="operadorpass123")
        url = reverse("producto_crear")
        data = {
            "nombre": "Tornillos Phillips",
            "descripcion": "Caja x 100",
            "categoria": self.cat.id,
            "precio_unitario": "0.00",
            "stock_minimo": 5,
            "stock_inicial": 20,
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        prod = Producto.objects.get(nombre="Tornillos Phillips")
        self.assertEqual(prod.stock_actual, 20)
        mov = Movimiento.objects.get(producto=prod)
        self.assertEqual(mov.created_by, self.user)
        self.assertEqual(mov.stock_anterior, 0)
        self.assertEqual(mov.stock_posterior, 20)

    def test_movimiento_historial_muestra_auditoria_saldos(self):
        registrar_entrada(self.producto.id, 8, observacion="Auditoría test")

        response = self.client.get(reverse("movimiento_historial"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "5")
        self.assertContains(response, "13 u.")
        self.assertContains(response, "Auditoría test")


class CatalogoReglasNegocioTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Limpieza General")
        self.prod = Producto.objects.create(
            nombre="Lavandina Concentrada",
            descripcion="Desinfectante clorado 55g/l",
            categoria=self.cat,
            stock_actual=10,
            stock_minimo=2,
            activo=True,
        )

    def test_unicidad_nombre_categoria_modelo_y_form(self):
        # A nivel modelo la duplicación debe arrojar IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Categoria.objects.create(nombre="Limpieza General")

        # A nivel formulario debe ser inválido
        form = CategoriaForm(data={"nombre": "Limpieza General"})
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_unicidad_nombre_producto_modelo_y_form(self):
        # A nivel modelo la duplicación debe arrojar IntegrityError
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Producto.objects.create(
                    nombre="Lavandina Concentrada",
                    categoria=self.cat,
                    stock_actual=5,
                )

        # A nivel formulario de alta
        form = ProductoCrearForm(
            data={
                "nombre": "Lavandina Concentrada",
                "categoria": self.cat.id,
                "stock_minimo": 1,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("nombre", form.errors)

    def test_baja_logica_desactiva_y_no_elimina_fisicamente(self):
        url = reverse("producto_desactivar", kwargs={"pk": self.prod.pk})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)

        # El producto sigue existiendo en BD pero con activo=False
        self.prod.refresh_from_db()
        self.assertFalse(self.prod.activo)
        self.assertTrue(Producto.objects.filter(pk=self.prod.pk).exists())

        # No debe aparecer en el listado activo
        list_url = reverse("producto_list")
        list_response = self.client.get(list_url)
        self.assertEqual(list_response.status_code, 200)
        nombres = [p.nombre for p in list_response.context["productos"]]
        self.assertNotIn("Lavandina Concentrada", nombres)

    def test_buscador_por_parte_del_nombre_y_por_descripcion(self):
        Producto.objects.create(
            nombre="Detergente Enzimático",
            descripcion="Desengrasante para cocina industrial",
            categoria=self.cat,
            stock_actual=5,
            stock_minimo=1,
            activo=True,
        )

        url = reverse("producto_list")

        # Búsqueda por parte del nombre ("Enzimático")
        resp_nombre = self.client.get(url, {"q": "Enzimático"})
        nombres_res = [p.nombre for p in resp_nombre.context["productos"]]
        self.assertIn("Detergente Enzimático", nombres_res)
        self.assertNotIn("Lavandina Concentrada", nombres_res)

        # Búsqueda por descripción ("cocina industrial")
        resp_desc = self.client.get(url, {"q": "cocina industrial"})
        nombres_res_desc = [p.nombre for p in resp_desc.context["productos"]]
        self.assertIn("Detergente Enzimático", nombres_res_desc)
        self.assertNotIn("Lavandina Concentrada", nombres_res_desc)

        # Búsqueda por descripción del primer producto ("clorado")
        resp_desc2 = self.client.get(url, {"q": "clorado"})
        nombres_res_desc2 = [p.nombre for p in resp_desc2.context["productos"]]
        self.assertIn("Lavandina Concentrada", nombres_res_desc2)
        self.assertNotIn("Detergente Enzimático", nombres_res_desc2)

    def test_producto_editar_actualiza_campos_y_no_modifica_stock(self):
        url = reverse("producto_editar", kwargs={"pk": self.prod.pk})
        data = {
            "nombre": "Lavandina Concentrada Plus",
            "descripcion": "Fórmula mejorada",
            "categoria": self.cat.id,
            "precio_unitario": str(self.prod.precio_unitario),
            "stock_minimo": 4,
            "stock_actual": 999,  # Intento malicioso de modificar stock_actual
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        self.prod.refresh_from_db()
        self.assertEqual(self.prod.nombre, "Lavandina Concentrada Plus")
        self.assertEqual(self.prod.descripcion, "Fórmula mejorada")
        self.assertEqual(self.prod.stock_minimo, 4)
        # El stock_actual debe mantenerse inalterado
        self.assertEqual(self.prod.stock_actual, 10)

    def test_proteccion_referencial_categoria_con_productos(self):
        with self.assertRaises(ProtectedError):
            self.cat.delete()
        self.assertTrue(Categoria.objects.filter(pk=self.cat.pk).exists())


class MovimientosReglasNegocioTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Químicos")
        self.prod_a = Producto.objects.create(
            nombre="Desinfectante Pino",
            categoria=self.cat,
            stock_actual=10,
            stock_minimo=2,
            activo=True,
        )
        self.prod_b = Producto.objects.create(
            nombre="Cera Autobrillo",
            categoria=self.cat,
            stock_actual=5,
            stock_minimo=1,
            activo=True,
        )

    def test_salida_mayor_al_stock_rechazada_en_servicio(self):
        with self.assertRaises(ValidationError) as ctx:
            registrar_salida(self.prod_a.id, cantidad=15)
        self.assertIn("Stock insuficiente", str(ctx.exception))
        self.prod_a.refresh_from_db()
        self.assertEqual(self.prod_a.stock_actual, 10)

    def test_salida_mayor_al_stock_rechazada_en_formulario(self):
        form_data = {
            "producto": self.prod_a.id,
            "tipo": Movimiento.TipoMovimiento.SALIDA,
            "cantidad": 15,
            "fecha": timezone.now().date(),
            "observacion": "Intento de sobre-egreso",
        }
        form = MovimientoUnificadoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("cantidad", form.errors)
        self.assertIn("Stock insuficiente", form.errors["cantidad"][0])

    def test_cantidades_cero_o_negativas_rechazadas_en_servicio(self):
        # Cantidad cero en entrada
        with self.assertRaises(ValidationError) as ctx_ent_zero:
            registrar_entrada(self.prod_a.id, cantidad=0)
        self.assertIn("mayor a cero", str(ctx_ent_zero.exception))

        # Cantidad negativa en entrada
        with self.assertRaises(ValidationError) as ctx_ent_neg:
            registrar_entrada(self.prod_a.id, cantidad=-5)
        self.assertIn("mayor a cero", str(ctx_ent_neg.exception))

        # Cantidad cero en salida
        with self.assertRaises(ValidationError) as ctx_sal_zero:
            registrar_salida(self.prod_a.id, cantidad=0)
        self.assertIn("mayor a cero", str(ctx_sal_zero.exception))

        # Cantidad negativa en salida
        with self.assertRaises(ValidationError) as ctx_sal_neg:
            registrar_salida(self.prod_a.id, cantidad=-3)
        self.assertIn("mayor a cero", str(ctx_sal_neg.exception))

    def test_cantidades_cero_o_negativas_rechazadas_en_formulario(self):
        # Entrada cantidad 0
        form_zero = MovimientoUnificadoForm(
            data={
                "producto": self.prod_a.id,
                "tipo": Movimiento.TipoMovimiento.ENTRADA,
                "cantidad": 0,
                "fecha": timezone.now().date(),
            }
        )
        self.assertFalse(form_zero.is_valid())
        self.assertIn("cantidad", form_zero.errors)

        # Salida cantidad 0
        form_sal_zero = MovimientoUnificadoForm(
            data={
                "producto": self.prod_a.id,
                "tipo": Movimiento.TipoMovimiento.SALIDA,
                "cantidad": 0,
                "fecha": timezone.now().date(),
            }
        )
        self.assertFalse(form_sal_zero.is_valid())
        self.assertIn("cantidad", form_sal_zero.errors)

        # Cantidad negativa (rechazada por min_value=0 del campo)
        form_neg = MovimientoUnificadoForm(
            data={
                "producto": self.prod_a.id,
                "tipo": Movimiento.TipoMovimiento.ENTRADA,
                "cantidad": -1,
                "fecha": timezone.now().date(),
            }
        )
        self.assertFalse(form_neg.is_valid())
        self.assertIn("cantidad", form_neg.errors)

    def test_ajuste_stock_real_negativo_rechazado_en_servicio(self):
        with self.assertRaises(ValidationError) as ctx:
            registrar_ajuste(self.prod_a.id, stock_real=-2)
        self.assertIn("no puede ser negativo", str(ctx.exception))
        self.prod_a.refresh_from_db()
        self.assertEqual(self.prod_a.stock_actual, 10)

    def test_filtros_historial_por_tipo_excluyen_otros_tipos(self):
        m_ent = registrar_entrada(self.prod_a.id, cantidad=2, observacion="Ingreso filtro")
        m_sal = registrar_salida(self.prod_a.id, cantidad=1, observacion="Salida filtro")
        m_ajuste = registrar_ajuste(self.prod_a.id, stock_real=20, observacion="Ajuste filtro")

        url = reverse("movimiento_historial")

        # Filtro por tipo SALIDA
        resp = self.client.get(url, {"tipo": "SALIDA"})
        self.assertEqual(resp.status_code, 200)
        movimientos = resp.context["movimientos"]
        mov_ids = [m.id for m in movimientos]

        self.assertIn(m_sal.id, mov_ids)
        self.assertNotIn(m_ent.id, mov_ids)
        self.assertNotIn(m_ajuste.id, mov_ids)

        # Filtro por tipo AJUSTE
        resp_aj = self.client.get(url, {"tipo": "AJUSTE"})
        self.assertEqual(resp_aj.status_code, 200)
        mov_aj_ids = [m.id for m in resp_aj.context["movimientos"]]

        self.assertIn(m_ajuste.id, mov_aj_ids)
        self.assertNotIn(m_ent.id, mov_aj_ids)
        self.assertNotIn(m_sal.id, mov_aj_ids)

    def test_filtros_historial_por_producto_excluyen_otros_productos(self):
        m_a = registrar_entrada(self.prod_a.id, cantidad=4, observacion="Producto A mov")
        m_b = registrar_entrada(self.prod_b.id, cantidad=3, observacion="Producto B mov")

        url = reverse("movimiento_historial")

        # Filtro por prod_a
        resp_a = self.client.get(url, {"producto": self.prod_a.id})
        self.assertEqual(resp_a.status_code, 200)
        ids_a = [m.id for m in resp_a.context["movimientos"]]
        self.assertIn(m_a.id, ids_a)
        self.assertNotIn(m_b.id, ids_a)

        # Filtro por prod_b
        resp_b = self.client.get(url, {"producto": self.prod_b.id})
        self.assertEqual(resp_b.status_code, 200)
        ids_b = [m.id for m in resp_b.context["movimientos"]]
        self.assertIn(m_b.id, ids_b)
        self.assertNotIn(m_a.id, ids_b)

    def test_fecha_retroactiva_guardada_exactamente_como_se_ingreso(self):
        url = reverse("movimiento_crear")
        fecha_pasada = datetime.date(2024, 3, 15)
        data = {
            "producto": self.prod_a.id,
            "tipo": "ENTRADA",
            "cantidad": 7,
            "fecha": fecha_pasada.strftime("%Y-%m-%d"),
            "observacion": "Carga de remito antiguo",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        movimiento = Movimiento.objects.filter(producto=self.prod_a, observacion="Carga de remito antiguo").first()
        self.assertIsNotNone(movimiento)
        # La fecha en el modelo debe coincidir exactamente con el día indicado
        self.assertEqual(movimiento.fecha.date(), fecha_pasada)
        self.assertEqual(movimiento.cantidad, 7)
        self.assertEqual(movimiento.tipo, Movimiento.TipoMovimiento.ENTRADA)


class MovimientoCrearInitialDataTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester', password='testpass')
        self.cat = Categoria.objects.create(nombre='TestCat')
        self.producto = Producto.objects.create(nombre='ProdTest', categoria=self.cat, stock_actual=5, stock_minimo=2)
        self.client.login(username='tester', password='testpass')

    def test_get_initial_data_prepopulates_form(self):
        url = reverse('movimiento_crear') + f'?producto={self.producto.id}&tipo=ENTRADA'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode()
        # product selected
        self.assertIn(f'value="{self.producto.id}" selected', content)
        # tipo selected
        self.assertIn('value="ENTRADA" selected', content)

class CategoriaViewsTest(TestCase):
    def setUp(self):
        # Category with active and inactive products
        self.cat_active = Categoria.objects.create(nombre="CatConProductos")
        # Active products
        Producto.objects.create(nombre="Prod A", categoria=self.cat_active, stock_actual=5, stock_minimo=2, activo=True)
        Producto.objects.create(nombre="Prod B", categoria=self.cat_active, stock_actual=3, stock_minimo=2, activo=True)
        # Inactive product
        Producto.objects.create(nombre="Prod C", categoria=self.cat_active, stock_actual=1, stock_minimo=2, activo=False)
        # Category without products
        self.cat_empty = Categoria.objects.create(nombre="CatVacia")

    def test_productos_activos_count(self):
        # Access the category list view
        response = self.client.get(reverse('categoria_list'))
        self.assertEqual(response.status_code, 200)
        categorias = response.context['categorias']
        # Find our category
        cat = next(c for c in categorias if c.id == self.cat_active.id)
        # Should have annotated count of active products = 2
        self.assertTrue(hasattr(cat, 'productos_activos'))
        self.assertEqual(cat.productos_activos, 2)
        # Empty category should have count 0
        cat_empty = next(c for c in categorias if c.id == self.cat_empty.id)
        self.assertTrue(hasattr(cat_empty, 'productos_activos'))
        self.assertEqual(cat_empty.productos_activos, 0)

    def test_template_contains_correct_link(self):
        response = self.client.get(reverse('categoria_list'))
        self.assertEqual(response.status_code, 200)
        # The link should point to producto_list with the category id as query param
        expected_href = f"{reverse('producto_list')}?categoria={self.cat_active.id}"
        self.assertIn(expected_href, response.content.decode())

    def test_link_filters_productos_por_categoria(self):
        # Access product list filtered by category
        url = reverse('producto_list') + f"?categoria={self.cat_active.id}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        productos = response.context['productos']
        # Only active products of the category should appear (inactive excluded by view)
        nombres = [p.nombre for p in productos]
        self.assertIn("Prod A", nombres)
        self.assertIn("Prod B", nombres)
        self.assertNotIn("Prod C", nombres)  # inactive should be excluded
        # Ensure no products from other categories appear
        self.assertNotIn("CatVacia", nombres)

    def test_categoria_list_crear_num_queries(self):
        # Ensure the view does not suffer N+1 queries
        with self.assertNumQueries(1):
            response = self.client.get(reverse('categoria_list'))
            self.assertEqual(response.status_code, 200)


class ClienteModelAndFormTest(TestCase):
    def test_dni_7_y_8_digitos_aceptado_en_modelo_y_normalizado(self):
        # DNI 7 dígitos
        c7 = Cliente(
            nombre="Cliente Siete",
            tipo_documento="DNI",
            numero_documento="7.123.456",
            domicilio="",
            telefono="",
        )
        c7.full_clean()
        c7.save()
        self.assertEqual(c7.numero_documento, "7123456")
        self.assertEqual(str(c7), "Cliente Siete (DNI 7123456)")

        # DNI 8 dígitos
        c8 = Cliente(
            nombre="Cliente Ocho",
            tipo_documento="DNI",
            numero_documento="40.123.456",
            domicilio="Av. Siempre Viva 123",
            telefono="11-4455-6677",
        )
        c8.full_clean()
        c8.save()
        self.assertEqual(c8.numero_documento, "40123456")
        self.assertEqual(c8.telefono, "1144556677")
        self.assertEqual(c8.domicilio, "Av. Siempre Viva 123")

    def test_dni_longitud_invalida_rechazado_en_modelo_y_form(self):
        # DNI 6 dígitos
        c_corto = Cliente(
            nombre="DNI Corto",
            tipo_documento="DNI",
            numero_documento="123456",
        )
        with self.assertRaises(ValidationError) as ctx:
            c_corto.full_clean()
        self.assertIn("numero_documento", ctx.exception.message_dict)

        # DNI 9 dígitos
        c_largo = Cliente(
            nombre="DNI Largo",
            tipo_documento="DNI",
            numero_documento="123456789",
        )
        with self.assertRaises(ValidationError) as ctx:
            c_largo.full_clean()
        self.assertIn("numero_documento", ctx.exception.message_dict)

        # En formulario
        form_corto = ClienteForm(data={
            "nombre": "Form DNI Corto",
            "tipo_documento": "DNI",
            "numero_documento": "123.456",
        })
        self.assertFalse(form_corto.is_valid())
        self.assertIn("numero_documento", form_corto.errors)

    def test_cuit_valido_aceptado_en_modelo_y_form(self):
        # CUIT real AFIP: 33-69345023-9 -> sum=145, 145%11=2, 11-2=9.
        c_afip = Cliente(
            nombre="AFIP",
            tipo_documento="CUIT",
            numero_documento="33-69345023-9",
        )
        c_afip.full_clean()
        c_afip.save()
        self.assertEqual(c_afip.numero_documento, "33693450239")

        # CUIT real YPF: 30-54668997-9 -> sum=233, 233%11=2, 11-2=9.
        form_ypf = ClienteForm(data={
            "nombre": "YPF S.A.",
            "tipo_documento": "CUIT",
            "numero_documento": "30-54668997-9",
            "domicilio": "Macacha Güemes 515",
            "correo": "contacto@ypf.com",
            "telefono": "01143446000",
        })
        self.assertTrue(form_ypf.is_valid())
        cliente_ypf = form_ypf.save()
        self.assertEqual(cliente_ypf.numero_documento, "30546689979")
        self.assertEqual(cliente_ypf.domicilio, "Macacha Güemes 515")

    def test_cuit_11_digitos_generico_aceptado(self):
        cuit_generico = Cliente(
            nombre="Empresa Test",
            tipo_documento="CUIT",
            numero_documento="20-12345678-0",
        )
        cuit_generico.full_clean()
        cuit_generico.save()
        self.assertEqual(cuit_generico.numero_documento, "20123456780")

    def test_cuit_longitud_distinta_a_11_rechazado(self):
        # CUIT 10 dígitos
        c_10 = Cliente(
            nombre="CUIT 10",
            tipo_documento="CUIT",
            numero_documento="3054668997",
        )
        with self.assertRaises(ValidationError) as ctx:
            c_10.full_clean()
        self.assertIn("numero_documento", ctx.exception.message_dict)

        # CUIT 12 dígitos
        c_12 = Cliente(
            nombre="CUIT 12",
            tipo_documento="CUIT",
            numero_documento="305466899791",
        )
        with self.assertRaises(ValidationError) as ctx:
            c_12.full_clean()
        self.assertIn("numero_documento", ctx.exception.message_dict)

        # En formulario
        form_10 = ClienteForm(data={
            "nombre": "CUIT 10 Form",
            "tipo_documento": "CUIT",
            "numero_documento": "3054668997",
        })
        self.assertFalse(form_10.is_valid())
        self.assertIn("numero_documento", form_10.errors)

    def test_telefono_corto_rechazado_y_vacio_aceptado(self):
        # Teléfono corto en modelo
        c_tel_corto = Cliente(
            nombre="Tel Corto",
            tipo_documento="DNI",
            numero_documento="30111222",
            telefono="12345",
        )
        with self.assertRaises(ValidationError) as ctx:
            c_tel_corto.full_clean()
        self.assertIn("telefono", ctx.exception.message_dict)

        # Teléfono corto en formulario
        form_tel_corto = ClienteForm(data={
            "nombre": "Tel Corto Form",
            "tipo_documento": "DNI",
            "numero_documento": "30111222",
            "telefono": "12345",
        })
        self.assertFalse(form_tel_corto.is_valid())
        self.assertIn("telefono", form_tel_corto.errors)

        # Teléfono vacío (opcional) aceptado
        form_tel_vacio = ClienteForm(data={
            "nombre": "Sin Teléfono",
            "tipo_documento": "DNI",
            "numero_documento": "30111222",
            "telefono": "",
        })
        self.assertTrue(form_tel_vacio.is_valid())

    def test_domicilio_puede_quedar_vacio(self):
        form = ClienteForm(data={
            "nombre": "Sin Domicilio",
            "tipo_documento": "DNI",
            "numero_documento": "31222333",
            "domicilio": "",
        })
        self.assertTrue(form.is_valid())
        cliente = form.save()
        self.assertEqual(cliente.domicilio, "")

    def test_rechazo_numero_documento_duplicado_en_modelo_y_form(self):
        Cliente.objects.create(
            nombre="Cliente Uno",
            tipo_documento="DNI",
            numero_documento="11223344",
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Cliente.objects.create(
                    nombre="Cliente Dos",
                    tipo_documento="DNI",
                    numero_documento="11223344",
                )

        # Mismo número con distinto formato en form
        form_duplicado = ClienteForm(data={
            "nombre": "Cliente Tres",
            "tipo_documento": "DNI",
            "numero_documento": "11.223.344",
        })
        self.assertFalse(form_duplicado.is_valid())
        self.assertIn("numero_documento", form_duplicado.errors)


class ClienteViewsTest(TestCase):
    def setUp(self):
        self.cliente_activo_1 = Cliente.objects.create(
            nombre="Carlos Gomez",
            tipo_documento="DNI",
            numero_documento="20111222",
            domicilio="Calle Falsa 123",
            correo="carlos@test.com",
            telefono="1144556677",
            activo=True,
        )
        self.cliente_activo_2 = Cliente.objects.create(
            nombre="Ana Fernandez",
            tipo_documento="CUIT",
            numero_documento="30546689979",
            domicilio="Av. Libertador 1000",
            correo="ana@test.com",
            telefono="1188990011",
            activo=True,
        )
        self.cliente_inactivo = Cliente.objects.create(
            nombre="Roberto Inactivo",
            tipo_documento=None,
            numero_documento=None,
            correo="roberto@test.com",
            telefono="1100000000",
            activo=False,
        )

    def test_alta_cliente_post_valido_crea_y_redirige(self):
        url = reverse("cliente_list")
        data = {
            "nombre": "Lucía Morales",
            "tipo_documento": "DNI",
            "numero_documento": "35.777.888",
            "domicilio": "San Martín 450",
            "correo": "lucia@test.com",
            "telefono": "1133221100",
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Cliente &#x27;Lucía Morales&#x27; registrado con éxito.")

        cliente = Cliente.objects.filter(numero_documento="35777888").first()
        self.assertIsNotNone(cliente)
        self.assertEqual(cliente.nombre, "Lucía Morales")
        self.assertEqual(cliente.tipo_documento, "DNI")
        self.assertEqual(cliente.domicilio, "San Martín 450")
        self.assertTrue(cliente.activo)

    def test_listado_solo_muestra_clientes_activos(self):
        url = reverse("cliente_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        nombres = [c.nombre for c in response.context["clientes"]]
        self.assertIn("Carlos Gomez", nombres)
        self.assertIn("Ana Fernandez", nombres)
        self.assertNotIn("Roberto Inactivo", nombres)
        self.assertContains(response, "DNI 20111222")
        self.assertContains(response, "CUIT 30546689979")
        self.assertContains(response, "Calle Falsa 123")

    def test_busqueda_por_documento_exacto_y_con_formato(self):
        url = reverse("cliente_list")

        # Búsqueda por número con formato
        resp_formato = self.client.get(url, {"q": "20.111.222"})
        nombres_formato = [c.nombre for c in resp_formato.context["clientes"]]
        self.assertIn("Carlos Gomez", nombres_formato)
        self.assertNotIn("Ana Fernandez", nombres_formato)

        # Búsqueda CUIT
        resp_cuit = self.client.get(url, {"q": "30-54668997-9"})
        nombres_cuit = [c.nombre for c in resp_cuit.context["clientes"]]
        self.assertIn("Ana Fernandez", nombres_cuit)
        self.assertNotIn("Carlos Gomez", nombres_cuit)

    def test_busqueda_por_nombre_parcial(self):
        url = reverse("cliente_list")
        resp = self.client.get(url, {"q": "Fernan"})
        nombres = [c.nombre for c in resp.context["clientes"]]
        self.assertIn("Ana Fernandez", nombres)
        self.assertNotIn("Carlos Gomez", nombres)

    def test_busqueda_por_id_exacto(self):
        url = reverse("cliente_list")
        resp = self.client.get(url, {"q": str(self.cliente_activo_1.id)})
        nombres = [c.nombre for c in resp.context["clientes"]]
        self.assertIn("Carlos Gomez", nombres)
        self.assertNotIn("Ana Fernandez", nombres)

    def test_baja_logica_desactiva_y_no_elimina_de_bd(self):
        url = reverse("cliente_desactivar", kwargs={"pk": self.cliente_activo_1.pk})
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)

        # Registro en BD debe seguir existiendo con activo=False
        self.cliente_activo_1.refresh_from_db()
        self.assertFalse(self.cliente_activo_1.activo)
        self.assertTrue(Cliente.objects.filter(pk=self.cliente_activo_1.pk).exists())

        # Ya no debe aparecer en el listado activo
        list_url = reverse("cliente_list")
        list_resp = self.client.get(list_url)
        nombres = [c.nombre for c in list_resp.context["clientes"]]
        self.assertNotIn("Carlos Gomez", nombres)

    def test_paginacion_clientes(self):
        # Crear 25 clientes adicionales con DNI válido de 8 dígitos
        for i in range(1, 26):
            Cliente.objects.create(
                nombre=f"Cliente Paginado {i:02d}",
                tipo_documento="DNI",
                numero_documento=f"500000{i:02d}",
                activo=True,
            )

        response = self.client.get(reverse("cliente_list"))
        self.assertEqual(response.status_code, 200)
        page_obj = response.context["page_obj"]

        # 2 clientes activos iniciales + 25 = 27 clientes activos
        self.assertEqual(page_obj.paginator.count, 27)
        self.assertEqual(len(page_obj), 15)
        self.assertTrue(page_obj.has_next())

        # Segunda página
        response_page2 = self.client.get(reverse("cliente_list"), {"page": 2})
        self.assertEqual(response_page2.status_code, 200)
        page_obj2 = response_page2.context["page_obj"]
        self.assertEqual(len(page_obj2), 12)
        self.assertFalse(page_obj2.has_next())


class ProveedorModelAndFormTest(TestCase):
    def test_dni_7_y_8_digitos_y_cuit_de_11_aceptados(self):
        proveedor_dni_7 = Proveedor(
            nombre="Proveedor DNI 7",
            tipo_documento="DNI",
            numero_documento="7.123.456",
        )
        proveedor_dni_7.full_clean()
        proveedor_dni_7.save()
        self.assertEqual(proveedor_dni_7.numero_documento, "7123456")

        proveedor_dni_8 = Proveedor(
            nombre="Proveedor DNI 8",
            tipo_documento="DNI",
            numero_documento="40.123.456",
        )
        proveedor_dni_8.full_clean()
        proveedor_dni_8.save()
        self.assertEqual(proveedor_dni_8.numero_documento, "40123456")

        proveedor_cuit = Proveedor(
            nombre="Proveedor CUIT",
            tipo_documento="CUIT",
            numero_documento="20-12345678-0",
        )
        proveedor_cuit.full_clean()
        proveedor_cuit.save()
        self.assertEqual(proveedor_cuit.numero_documento, "20123456780")

    def test_longitudes_invalidas_rechazadas_en_modelo_y_formulario(self):
        for tipo, numero in (("DNI", "123456"), ("DNI", "123456789"), ("CUIT", "3054668997"), ("CUIT", "305466899791")):
            with self.subTest(tipo=tipo, numero=numero):
                proveedor = Proveedor(
                    nombre="Documento inválido",
                    tipo_documento=tipo,
                    numero_documento=numero,
                )
                with self.assertRaises(ValidationError) as ctx:
                    proveedor.full_clean()
                self.assertIn("numero_documento", ctx.exception.message_dict)

                form = ProveedorForm(data={
                    "nombre": "Documento inválido",
                    "tipo_documento": tipo,
                    "numero_documento": numero,
                })
                self.assertFalse(form.is_valid())
                self.assertIn("numero_documento", form.errors)

    def test_rechazo_numero_documento_duplicado_en_modelo_y_formulario(self):
        Proveedor.objects.create(
            nombre="Proveedor Uno",
            tipo_documento="DNI",
            numero_documento="11223344",
        )
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                Proveedor.objects.create(
                    nombre="Proveedor Dos",
                    tipo_documento="DNI",
                    numero_documento="11223344",
                )

        form_duplicado = ProveedorForm(data={
            "nombre": "Proveedor Tres",
            "tipo_documento": "DNI",
            "numero_documento": "11.223.344",
        })
        self.assertFalse(form_duplicado.is_valid())
        self.assertIn("numero_documento", form_duplicado.errors)


class ProveedorViewsTest(TestCase):
    def setUp(self):
        self.proveedor_activo_1 = Proveedor.objects.create(
            nombre="Distribuidora Norte",
            tipo_documento="DNI",
            numero_documento="20111222",
            domicilio="Calle Falsa 123",
            correo="norte@test.com",
            telefono="1144556677",
        )
        self.proveedor_activo_2 = Proveedor.objects.create(
            nombre="Insumos Fernandez",
            tipo_documento="CUIT",
            numero_documento="30546689979",
            domicilio="Av. Libertador 1000",
            correo="fernandez@test.com",
            telefono="1188990011",
        )
        self.proveedor_inactivo = Proveedor.objects.create(
            nombre="Proveedor Inactivo",
            tipo_documento="DNI",
            numero_documento="12345678",
            activo=False,
        )

    def test_alta_proveedor_valida_y_resalta_seccion_activa(self):
        response = self.client.post(
            reverse("proveedor_list"),
            {
                "nombre": "Lucía Insumos",
                "tipo_documento": "DNI",
                "numero_documento": "35.777.888",
                "domicilio": "San Martín 450",
                "correo": "lucia@test.com",
                "telefono": "1133221100",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Proveedor &#x27;Lucía Insumos&#x27; registrado con éxito.")
        self.assertContains(response, 'href="/proveedores/" class="sidebar-link active"')

        proveedor = Proveedor.objects.get(numero_documento="35777888")
        self.assertEqual(proveedor.nombre, "Lucía Insumos")
        self.assertEqual(proveedor.tipo_documento, "DNI")
        self.assertTrue(proveedor.activo)

    def test_listado_solo_muestra_proveedores_activos(self):
        response = self.client.get(reverse("proveedor_list"))
        self.assertEqual(response.status_code, 200)

        nombres = [proveedor.nombre for proveedor in response.context["proveedores"]]
        self.assertIn("Distribuidora Norte", nombres)
        self.assertIn("Insumos Fernandez", nombres)
        self.assertNotIn("Proveedor Inactivo", nombres)
        self.assertContains(response, "DNI 20111222")
        self.assertContains(response, "CUIT 30546689979")

    def test_busqueda_por_documento_formateado(self):
        response = self.client.get(reverse("proveedor_list"), {"q": "30-54668997-9"})
        nombres = [proveedor.nombre for proveedor in response.context["proveedores"]]
        self.assertIn("Insumos Fernandez", nombres)
        self.assertNotIn("Distribuidora Norte", nombres)

    def test_busqueda_por_nombre_parcial(self):
        response = self.client.get(reverse("proveedor_list"), {"q": "Fernan"})
        nombres = [proveedor.nombre for proveedor in response.context["proveedores"]]
        self.assertIn("Insumos Fernandez", nombres)
        self.assertNotIn("Distribuidora Norte", nombres)

    def test_busqueda_por_id_exacto(self):
        response = self.client.get(
            reverse("proveedor_list"),
            {"q": str(self.proveedor_activo_1.id)},
        )
        nombres = [proveedor.nombre for proveedor in response.context["proveedores"]]
        self.assertEqual(nombres, ["Distribuidora Norte"])

    def test_baja_logica_confirma_desactiva_y_no_elimina(self):
        url = reverse("proveedor_desactivar", kwargs={"pk": self.proveedor_activo_1.pk})
        confirmacion = self.client.get(url)
        self.assertEqual(confirmacion.status_code, 200)
        self.assertContains(confirmacion, "Distribuidora Norte")
        self.assertContains(confirmacion, 'href="/proveedores/" class="sidebar-link active"')

        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.proveedor_activo_1.refresh_from_db()
        self.assertFalse(self.proveedor_activo_1.activo)
        self.assertTrue(Proveedor.objects.filter(pk=self.proveedor_activo_1.pk).exists())

        nombres = [proveedor.nombre for proveedor in response.context["proveedores"]]
        self.assertNotIn("Distribuidora Norte", nombres)

    def test_paginacion_proveedores(self):
        for i in range(1, 26):
            Proveedor.objects.create(
                nombre=f"Proveedor Paginado {i:02d}",
                tipo_documento="DNI",
                numero_documento=f"500000{i:02d}",
            )

        response = self.client.get(reverse("proveedor_list"))
        page_obj = response.context["page_obj"]
        self.assertEqual(page_obj.paginator.count, 27)
        self.assertEqual(len(page_obj), 15)
        self.assertTrue(page_obj.has_next())

        response_page2 = self.client.get(reverse("proveedor_list"), {"page": 2})
        page_obj2 = response_page2.context["page_obj"]
        self.assertEqual(len(page_obj2), 12)
        self.assertFalse(page_obj2.has_next())


class PedidosServicesTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="vendedor", password="password123")
        self.cat = Categoria.objects.create(nombre="Limpieza")
        self.cliente = Cliente.objects.create(
            nombre="Empresa Test S.A.",
            tipo_documento="CUIT",
            numero_documento="30712345678",
            domicilio="Calle Falsa 123",
            telefono="1144556677",
        )
        self.prod1 = Producto.objects.create(
            nombre="Detergente 5L",
            categoria=self.cat,
            precio_unitario=Decimal("1500.50"),
            stock_actual=20,
            stock_minimo=5,
        )
        self.prod2 = Producto.objects.create(
            nombre="Lavandina 5L",
            categoria=self.cat,
            precio_unitario=Decimal("800.00"),
            stock_actual=10,
            stock_minimo=2,
        )

    def test_creacion_exitosa_pedido_y_descuento_automatico_stock(self):
        items_data = [
            {"producto_id": self.prod1.id, "cantidad": 4},
            {"producto_id": self.prod2.id, "cantidad": 2},
        ]
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=items_data,
            usuario=self.user,
            observacion="Entrega prioritaria",
        )

        self.assertEqual(pedido.estado, Pedido.EstadoPedido.CONFIRMADO)
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.items.count(), 2)
        self.assertTrue(pedido.numero_operacion.startswith(f"{timezone.now().year}-"))

        # Descuento de stock en productos
        self.prod1.refresh_from_db()
        self.prod2.refresh_from_db()
        self.assertEqual(self.prod1.stock_actual, 16)
        self.assertEqual(self.prod2.stock_actual, 8)

        # Validación de ítems y precios congelados
        item1 = pedido.items.get(producto=self.prod1)
        item2 = pedido.items.get(producto=self.prod2)
        self.assertEqual(item1.precio_unitario, Decimal("1500.50"))
        self.assertEqual(item1.subtotal, Decimal("6002.00"))
        self.assertEqual(item2.precio_unitario, Decimal("800.00"))
        self.assertEqual(item2.subtotal, Decimal("1600.00"))
        self.assertEqual(pedido.total, Decimal("7602.00"))

        # Modificación posterior de precio de catálogo NO altera precio histórico
        self.prod1.precio_unitario = Decimal("2500.00")
        self.prod1.save()
        item1.refresh_from_db()
        self.assertEqual(item1.precio_unitario, Decimal("1500.50"))

        # Verificación de movimientos de auditoría
        movs = Movimiento.objects.filter(pedido=pedido)
        self.assertEqual(movs.count(), 2)
        for m in movs:
            self.assertEqual(m.tipo, Movimiento.TipoMovimiento.SALIDA)
            self.assertEqual(m.created_by, self.user)
            self.assertEqual(m.pedido, pedido)

    def test_rechazo_pedido_por_stock_insuficiente_rollback_atomico(self):
        # prod1 tiene 20 u. disponible, prod2 tiene 10 u. Pedimos 15 de prod2 (insuficiente)
        items_data = [
            {"producto_id": self.prod1.id, "cantidad": 5},
            {"producto_id": self.prod2.id, "cantidad": 15},
        ]

        with self.assertRaises(ValidationError) as ctx:
            crear_pedido(
                cliente_id=self.cliente.id,
                items_data=items_data,
                usuario=self.user,
            )

        self.assertIn("Stock insuficiente", str(ctx.exception))

        # Rollback atómico completo: no se crea pedido ni movimientos
        self.assertEqual(Pedido.objects.count(), 0)
        self.assertEqual(PedidoItem.objects.count(), 0)
        self.assertEqual(Movimiento.objects.count(), 0)

        # Stock de ambos productos intacto
        self.prod1.refresh_from_db()
        self.prod2.refresh_from_db()
        self.assertEqual(self.prod1.stock_actual, 20)
        self.assertEqual(self.prod2.stock_actual, 10)

    def test_cancelacion_pedido_y_movimientos_compensatorios(self):
        items_data = [
            {"producto_id": self.prod1.id, "cantidad": 3},
            {"producto_id": self.prod2.id, "cantidad": 2},
        ]
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=items_data,
            usuario=self.user,
        )

        self.prod1.refresh_from_db()
        self.prod2.refresh_from_db()
        self.assertEqual(self.prod1.stock_actual, 17)
        self.assertEqual(self.prod2.stock_actual, 8)

        # Cancelar pedido
        pedido_cancelado = cancelar_pedido(
            pedido_id=pedido.id,
            usuario=self.user,
            motivo="Cliente canceló la orden",
        )

        self.assertEqual(pedido_cancelado.estado, Pedido.EstadoPedido.CANCELADO)
        self.assertIn("Cliente canceló la orden", pedido_cancelado.observacion)

        # Stock restituido
        self.prod1.refresh_from_db()
        self.prod2.refresh_from_db()
        self.assertEqual(self.prod1.stock_actual, 20)
        self.assertEqual(self.prod2.stock_actual, 10)

        # Movimientos: 2 de salida originales + 2 de entrada compensatorios = 4
        movs = Movimiento.objects.filter(pedido=pedido)
        self.assertEqual(movs.count(), 4)
        entradas = movs.filter(tipo=Movimiento.TipoMovimiento.ENTRADA)
        self.assertEqual(entradas.count(), 2)
        for ent in entradas:
            self.assertIn("Compensación por cancelación", ent.observacion)

        # Re-cancelar debe arrojar error
        with self.assertRaises(ValidationError) as ctx:
            cancelar_pedido(pedido_id=pedido.id)
        self.assertIn("ya se encuentra cancelado", str(ctx.exception))

    def test_asignacion_correlativo_anual_seguro(self):
        anio_actual = timezone.now().year
        p1 = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.prod1.id, "cantidad": 1}],
        )
        p2 = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.prod1.id, "cantidad": 1}],
        )

        self.assertEqual(p1.numero_operacion, f"{anio_actual}-0001")
        self.assertEqual(p2.numero_operacion, f"{anio_actual}-0002")

        # Pedido en otro año calendario
        fecha_otro_anio = timezone.make_aware(datetime.datetime(anio_actual + 1, 1, 15, 10, 0))
        p_otro = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.prod1.id, "cantidad": 1}],
            fecha=fecha_otro_anio,
        )
        self.assertEqual(p_otro.numero_operacion, f"{anio_actual + 1}-0001")

    def test_compatibilidad_registrar_entrada_salida_sin_pedido(self):
        # Movimiento manual sin pedido (retrocompatibilidad)
        m_ent = registrar_entrada(
            producto_id=self.prod1.id,
            cantidad=5,
            observacion="Ingreso general",
        )
        self.assertIsNone(m_ent.pedido)

        m_sal = registrar_salida(
            producto_id=self.prod1.id,
            cantidad=2,
            observacion="Merma",
        )
        self.assertIsNone(m_sal.pedido)


class OrdenesCompraServicesTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Insumos")
        self.proveedor = Proveedor.objects.create(
            nombre="Distribuidora Test",
            tipo_documento="CUIT",
            numero_documento="30765432109",
        )
        self.producto = Producto.objects.create(
            nombre="Caja de tornillos",
            categoria=self.cat,
            precio_unitario=Decimal("25.00"),
            stock_actual=10,
            stock_minimo=2,
        )

    def crear_orden(self):
        return crear_orden_compra(
            proveedor_id=self.proveedor.id,
            items_data=[
                {
                    "producto_id": self.producto.id,
                    "cantidad": 4,
                    "precio_unitario_compra": Decimal("18.50"),
                }
            ],
        )

    def test_crear_orden_no_modifica_stock(self):
        orden = self.crear_orden()

        self.producto.refresh_from_db()
        self.assertEqual(orden.estado, OrdenCompra.EstadoOrdenCompra.PENDIENTE)
        self.assertEqual(self.producto.stock_actual, 10)
        self.assertFalse(Movimiento.objects.filter(orden_compra=orden).exists())

    def test_recibir_mercaderia_incrementa_stock_y_cambia_estado(self):
        orden = self.crear_orden()

        recibida = recibir_mercaderia(orden_compra_id=orden.id)

        self.producto.refresh_from_db()
        self.assertEqual(recibida.estado, OrdenCompra.EstadoOrdenCompra.RECIBIDA)
        self.assertEqual(self.producto.stock_actual, 14)
        movimiento = Movimiento.objects.get(orden_compra=orden)
        self.assertEqual(movimiento.tipo, Movimiento.TipoMovimiento.ENTRADA)
        self.assertEqual(movimiento.cantidad, 4)

    def test_recibir_orden_ya_recibida_es_rechazado(self):
        orden = self.crear_orden()
        recibir_mercaderia(orden_compra_id=orden.id)

        with self.assertRaises(ValidationError):
            recibir_mercaderia(orden_compra_id=orden.id)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 14)
        self.assertEqual(Movimiento.objects.filter(orden_compra=orden).count(), 1)

    def test_cancelar_orden_pendiente_no_genera_movimientos(self):
        orden = self.crear_orden()

        cancelada = cancelar_orden_compra(orden_compra_id=orden.id)

        self.producto.refresh_from_db()
        self.assertEqual(cancelada.estado, OrdenCompra.EstadoOrdenCompra.CANCELADA)
        self.assertEqual(self.producto.stock_actual, 10)
        self.assertFalse(Movimiento.objects.filter(orden_compra=orden).exists())

    def test_cancelar_orden_cancelada_o_recibida_es_rechazado(self):
        cancelada = self.crear_orden()
        cancelar_orden_compra(orden_compra_id=cancelada.id)
        recibida = self.crear_orden()
        recibir_mercaderia(orden_compra_id=recibida.id)

        with self.assertRaises(ValidationError):
            cancelar_orden_compra(orden_compra_id=cancelada.id)
        with self.assertRaises(ValidationError):
            cancelar_orden_compra(orden_compra_id=recibida.id)

    def test_numero_orden_compra_no_colisiona_con_pedido_del_mismo_anio(self):
        pedido = crear_pedido(
            cliente_id=Cliente.objects.create(
                nombre="Cliente de prueba",
                tipo_documento="DNI",
                numero_documento="30123456",
            ).id,
            items_data=[{"producto_id": self.producto.id, "cantidad": 1}],
        )
        orden = self.crear_orden()
        anio_actual = timezone.now().year

        self.assertEqual(pedido.numero_operacion, f"{anio_actual}-0001")
        self.assertEqual(orden.numero_operacion, f"OC-{anio_actual}-0001")
        self.assertNotEqual(pedido.numero_operacion, orden.numero_operacion)

    def test_movimiento_de_recepcion_muestra_orden_asociada_en_historial(self):
        orden = self.crear_orden()
        recibir_mercaderia(orden_compra_id=orden.id)

        response = self.client.get(reverse("movimiento_historial"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f"Orden de Compra #{orden.numero_operacion}")
        self.assertContains(
            response,
            reverse("orden_compra_detalle", kwargs={"pk": orden.id}),
        )


class ProductoCrearAjaxViewTest(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Herramientas rápidas")

    def test_crea_producto_y_devuelve_datos_json(self):
        response = self.client.post(
            reverse("producto_crear_ajax"),
            {
                "nombre": "Llave inglesa",
                "categoria": self.categoria.id,
                "precio_unitario": "1250.00",
                "stock_minimo": 3,
                "descripcion": "",
                "stock_inicial": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            data,
            {
                "success": True,
                "id": Producto.objects.get(nombre="Llave inglesa").id,
                "nombre": "Llave inglesa",
            },
        )
        producto = Producto.objects.get(pk=data["id"])
        self.assertEqual(producto.stock_actual, 2)
        self.assertTrue(Movimiento.objects.filter(producto=producto).exists())

    def test_producto_invalido_devuelve_errores_del_formulario(self):
        response = self.client.post(
            reverse("producto_crear_ajax"),
            {
                "nombre": "",
                "categoria": self.categoria.id,
                "precio_unitario": "1250.00",
                "stock_minimo": 3,
                "descripcion": "",
                "stock_inicial": 0,
            },
        )

        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("nombre", data["errors"])
        self.assertFalse(Producto.objects.exists())


class PedidosViewsAndFormsTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="operador_ventas", password="password123")
        self.cat = Categoria.objects.create(nombre="Bazar")
        self.cliente = Cliente.objects.create(
            nombre="Juan Perez",
            tipo_documento="DNI",
            numero_documento="30111222",
            domicilio="Av. Mitre 500",
            telefono="1122334455",
        )
        self.producto = Producto.objects.create(
            nombre="Escoba Plástica",
            categoria=self.cat,
            precio_unitario=Decimal("950.00"),
            stock_actual=15,
            stock_minimo=3,
        )

    def test_pedido_list_view_render_y_filtros(self):
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.producto.id, "cantidad": 2}],
        )

        response = self.client.get(reverse("pedido_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pedido.numero_operacion)
        self.assertContains(response, "Juan Perez")

        # Filtro por número de operación
        resp_filtro = self.client.get(reverse("pedido_list"), {"q": pedido.numero_operacion})
        self.assertEqual(resp_filtro.status_code, 200)
        self.assertContains(resp_filtro, pedido.numero_operacion)

        # Filtro por estado
        resp_estado = self.client.get(reverse("pedido_list"), {"estado": "CONFIRMADO"})
        self.assertEqual(resp_estado.status_code, 200)
        self.assertContains(resp_estado, pedido.numero_operacion)

    def test_pedido_crear_view_post_exitoso(self):
        self.client.login(username="operador_ventas", password="password123")
        url = reverse("pedido_crear")
        data = {
            "cliente": self.cliente.id,
            "fecha": timezone.now().date().strftime("%Y-%m-%d"),
            "observacion": "Pedido vía web",
            # Formset management fields
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
            "items-0-producto": self.producto.id,
            "items-0-cantidad": "3",
        }

        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)

        pedido = Pedido.objects.latest("id")
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.items.count(), 1)
        self.assertEqual(pedido.items.first().cantidad, 3)

        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 12)

    def test_pedido_crear_view_stock_insuficiente_muestra_error(self):
        self.client.login(username="operador_ventas", password="password123")
        url = reverse("pedido_crear")
        data = {
            "cliente": self.cliente.id,
            "fecha": timezone.now().date().strftime("%Y-%m-%d"),
            "observacion": "Pedido excesivo",
            "items-TOTAL_FORMS": "1",
            "items-INITIAL_FORMS": "0",
            "items-MIN_NUM_FORMS": "0",
            "items-MAX_NUM_FORMS": "1000",
            "items-0-producto": self.producto.id,
            "items-0-cantidad": "50",  # Hay solo 15
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Pedido.objects.count(), 0)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 15)

    def test_pedido_detalle_view(self):
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.producto.id, "cantidad": 2}],
        )
        url = reverse("pedido_detalle", kwargs={"pk": pedido.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, pedido.numero_operacion)
        self.assertContains(response, "Escoba Plástica")
        self.assertContains(response, "$1900,00")

    def test_pedido_y_remito_conservan_datos_historicos(self):
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.producto.id, "cantidad": 2}],
        )

        self.cliente.nombre = "Nombre actualizado"
        self.cliente.numero_documento = "30123456"
        self.cliente.telefono = "1199999999"
        self.cliente.save()
        self.producto.nombre = "Producto actualizado"
        self.producto.save()

        response = self.client.get(reverse("pedido_detalle", kwargs={"pk": pedido.pk}))
        self.assertContains(response, "Juan Perez")
        self.assertContains(response, "30111222")
        self.assertContains(response, "Escoba Plástica")
        self.assertNotContains(response, "Nombre actualizado")
        self.assertNotContains(response, "Producto actualizado")

        remito = render_to_string("inventario/pdf/remito.html", {"pedido": pedido})
        self.assertIn("Juan Perez", remito)
        self.assertIn("30111222", remito)
        self.assertIn("1122334455", remito)
        self.assertIn("Escoba Plástica", remito)
        self.assertNotIn("Nombre actualizado", remito)
        self.assertNotIn("Producto actualizado", remito)

    def test_pedido_pdf_view_retorna_pdf_descargable(self):
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.producto.id, "cantidad": 2}],
        )

        response = self.client.get(reverse("pedido_pdf", kwargs={"pk": pedido.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertIn(
            f'Remito_{pedido.numero_operacion}.pdf', response["Content-Disposition"]
        )

    def test_pedido_cancelar_view_post(self):
        self.client.login(username="operador_ventas", password="password123")
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.producto.id, "cantidad": 4}],
        )
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 11)

        url = reverse("pedido_cancelar", kwargs={"pk": pedido.pk})
        response = self.client.post(url, {"motivo": "Cancelado por error"}, follow=True)
        self.assertEqual(response.status_code, 200)

        pedido.refresh_from_db()
        self.assertEqual(pedido.estado, Pedido.EstadoPedido.CANCELADO)
        self.producto.refresh_from_db()
        self.assertEqual(self.producto.stock_actual, 15)


class CajaFeatureTest(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nombre="Caja")
        self.cliente = Cliente.objects.create(
            nombre="Cliente Caja",
            tipo_documento="DNI",
            numero_documento="32123456",
        )
        self.producto = Producto.objects.create(
            nombre="Producto Caja",
            categoria=self.categoria,
            precio_unitario=Decimal("12.35"),
            stock_actual=10,
            stock_minimo=1,
        )

    def test_pedido_y_cancelacion_registran_movimientos_compensatorios(self):
        pedido = crear_pedido(
            cliente_id=self.cliente.id,
            items_data=[{"producto_id": self.producto.id, "cantidad": 2}],
        )

        ingreso = MovimientoCaja.objects.get(pedido=pedido)
        self.assertEqual(ingreso.tipo, MovimientoCaja.TipoMovimientoCaja.INGRESO)
        self.assertEqual(ingreso.monto, Decimal("24.70"))

        cancelar_pedido(pedido_id=pedido.id, motivo="Prueba de caja")

        egreso = MovimientoCaja.objects.get(
            pedido=pedido,
            tipo=MovimientoCaja.TipoMovimientoCaja.EGRESO,
        )
        self.assertEqual(egreso.monto, ingreso.monto)
        self.assertEqual(MovimientoCaja.objects.filter(pedido=pedido).count(), 2)

    def test_dashboard_calcula_saldo_decimal_y_admite_movimientos_sin_pedido(self):
        MovimientoCaja.objects.create(
            tipo=MovimientoCaja.TipoMovimientoCaja.INGRESO,
            monto=Decimal("100.10"),
            concepto="Ingreso de prueba",
        )
        MovimientoCaja.objects.create(
            tipo=MovimientoCaja.TipoMovimientoCaja.EGRESO,
            monto=Decimal("20.05"),
            concepto="Egreso de prueba",
        )

        response = self.client.get(reverse("caja_dashboard"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_ingresos"], Decimal("100.10"))
        self.assertEqual(response.context["total_egresos"], Decimal("20.05"))
        self.assertEqual(response.context["saldo"], Decimal("80.05"))
        self.assertTrue(
            MovimientoCaja.objects.filter(pedido__isnull=True).exists()
        )
        self.assertNotRegex(response.content.decode(), r"\bstyle\s*=")

    def test_egreso_manual_valida_y_registra_el_concepto(self):
        form = EgresoCajaForm(data={"monto": "0", "concepto": "Gasto inválido"})
        self.assertFalse(form.is_valid())
        self.assertIn("monto", form.errors)

        response = self.client.post(
            reverse("caja_egreso_crear"),
            {"monto": "15.25", "concepto": "Compra de limpieza"},
        )

        self.assertRedirects(response, reverse("caja_dashboard"))
        egreso = MovimientoCaja.objects.get()
        self.assertEqual(egreso.tipo, MovimientoCaja.TipoMovimientoCaja.EGRESO)
        self.assertEqual(egreso.monto, Decimal("15.25"))
        self.assertEqual(egreso.concepto, "Compra de limpieza")
        self.assertIsNone(egreso.pedido)

        dashboard = self.client.get(reverse("caja_dashboard"))
        formulario = self.client.get(reverse("caja_egreso_crear"))
        self.assertEqual(dashboard.status_code, 200)
        self.assertEqual(formulario.status_code, 200)
        self.assertNotRegex(formulario.content.decode(), r"\bstyle\s*=")


class BackupDownloadTest(TransactionTestCase):
    def test_backup_descargado_es_una_base_sqlite_integra(self):
        Categoria.objects.create(nombre="Respaldo")

        response = self.client.get(reverse("descargar_backup"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/vnd.sqlite3")
        self.assertIn("attachment; filename=\"backup_", response["Content-Disposition"])
        backup_data = b"".join(response.streaming_content)
        self.assertTrue(backup_data.startswith(b"SQLite format 3\x00"))

        backup_connection = sqlite3.connect(":memory:")
        try:
            backup_connection.deserialize(backup_data)
            integrity = backup_connection.execute("PRAGMA integrity_check").fetchone()[0]
            self.assertEqual(integrity, "ok")
            self.assertTrue(
                backup_connection.execute(
                    "SELECT 1 FROM inventario_categoria WHERE nombre = ?", ("Respaldo",)
                ).fetchone()
            )
        finally:
            backup_connection.close()


class ProductoPrecioUnitarioTest(TestCase):
    def setUp(self):
        self.cat = Categoria.objects.create(nombre="Higiene")

    def test_producto_crear_con_precio_unitario(self):
        form_data = {
            "nombre": "Jabón Líquido 500ml",
            "categoria": self.cat.id,
            "precio_unitario": "350.75",
            "stock_minimo": 10,
            "stock_inicial": 25,
        }
        form = ProductoCrearForm(data=form_data)
        self.assertTrue(form.is_valid())
        prod = form.save()
        self.assertEqual(prod.precio_unitario, Decimal("350.75"))

    def test_producto_editar_actualiza_precio_unitario(self):
        prod = Producto.objects.create(
            nombre="Jabón en Barra",
            categoria=self.cat,
            precio_unitario=Decimal("100.00"),
            stock_actual=10,
            stock_minimo=2,
        )
        form_data = {
            "nombre": "Jabón en Barra",
            "categoria": self.cat.id,
            "precio_unitario": "145.50",
            "stock_minimo": 2,
        }
        form = ProductoEditarForm(data=form_data, instance=prod)
        self.assertTrue(form.is_valid())
        form.save()
        prod.refresh_from_db()
        self.assertEqual(prod.precio_unitario, Decimal("145.50"))

    def test_export_csv_incluye_precio_unitario(self):
        Producto.objects.create(
            nombre="Desodorante Ambiental",
            categoria=self.cat,
            precio_unitario=Decimal("450.00"),
            stock_actual=8,
            stock_minimo=2,
        )
        response = self.client.get(reverse("export_csv"))
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")
        self.assertIn("Precio Unitario de Venta", content)
        self.assertIn("$450.00", content)
