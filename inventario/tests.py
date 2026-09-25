import datetime

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.db.models.query import QuerySet
from django.template import Context, Template
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from inventario.admin import MovimientoAdmin
from inventario.forms import (
    CategoriaForm,
    MovimientoUnificadoForm,
    ProductoCrearForm,
    ProductoEditarForm,
)
from inventario.models import Categoria, Movimiento, Producto
from inventario.services import (
    registrar_ajuste,
    registrar_entrada,
    registrar_salida,
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
