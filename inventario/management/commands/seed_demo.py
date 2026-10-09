import random
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from inventario.models import (
    Categoria,
    Cliente,
    OrdenCompra,
    OrdenCompraItem,
    Pedido,
    PedidoItem,
    Producto,
    Proveedor,
)


class Command(BaseCommand):
    help = "Carga datos de prueba coherentes para cada entidad del sistema"

    def handle(self, *args, **options):
        self.stdout.write("Iniciando carga de datos de prueba...")

        # 1. Categorías (20)
        nombres_cat = [
            "Lavandinas y Clorados",
            "Detergentes y Desengrasantes",
            "Limpiadores de Pisos",
            "Cuidado de Ropa",
            "Papelería Institucional",
            "Bolsas de Residuos",
            "Accesorios de Limpieza",
            "Desinfectantes Ambientales",
            "Higiene Personal",
            "Limpiavidrios y Cristales",
            "Limpia Metales y Quitaóxidos",
            "Ceras y Autobrillos",
            "Quitamanchas y Solventes",
            "Pastillas para Inodoro",
            "Guantes y Protección",
            "Esponjas y Fibras",
            "Insecticidas y Repelentes",
            "Aromatización Continua",
            "Productos para Autos",
            "Químicos Clorados Concentrados",
        ]

        categorias = []
        for nombre in nombres_cat:
            cat, _ = Categoria.objects.get_or_create(nombre=nombre)
            categorias.append(cat)
        self.stdout.write(self.style.SUCCESS("OK: 20 Categorias listas."))

        # 2. Productos (20)
        datos_productos = [
            ("Lavandina Concentrada 1L", categorias[0], "550.00", 15, 80),
            ("Lavandina en Gel 750ml", categorias[0], "820.00", 10, 45),
            ("Detergente Magistral Limón 500ml", categorias[1], "1250.00", 20, 110),
            ("Desengrasante Industrial Alcalino 5L", categorias[1], "4800.00", 5, 25),
            ("Desodorante de Piso Pino 5L", categorias[2], "2200.00", 12, 60),
            ("Limpiador Líquido Lavanda 900ml", categorias[2], "750.00", 15, 70),
            ("Jabón Líquido Baja Espuma 3L", categorias[3], "3600.00", 8, 40),
            ("Suavizante Textil Celeste 3L", categorias[3], "2900.00", 8, 35),
            ("Bobina Papel Kraft 400m", categorias[4], "5100.00", 6, 20),
            ("Toallas Intercaladas Blancas x2000", categorias[4], "4400.00", 10, 30),
            ("Bolsas Consorcio 80x110 x10", categorias[5], "1950.00", 25, 120),
            ("Bolsas Residuos 45x55 x30", categorias[5], "980.00", 20, 95),
            ("Secador de Goma Reforzado 40cm", categorias[6], "2100.00", 10, 35),
            ("Mopa Algodón Roscada 300g", categorias[6], "2600.00", 8, 28),
            ("Aerosol Desinfectante Lysoform 360cc", categorias[7], "1850.00", 15, 55),
            ("Alcohol en Gel con Dosificador 500ml", categorias[8], "1350.00", 12, 50),
            ("Limpiavidrios con Gatillo 500ml", categorias[9], "920.00", 10, 40),
            ("Guantes Látex Limpieza Talle M", categorias[14], "1100.00", 30, 150),
            ("Esponja Fibra Verde Pack x3", categorias[15], "650.00", 25, 90),
            ("Pastillas de Cloro Triple Acción 1kg", categorias[19], "6200.00", 5, 18),
        ]

        productos = []
        for nombre, cat, precio, stock_min, stock_act in datos_productos:
            prod, _ = Producto.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "categoria": cat,
                    "descripcion": f"Producto estándar de catálogo: {nombre}",
                    "precio_unitario": Decimal(precio),
                    "stock_minimo": stock_min,
                    "stock_actual": stock_act,
                    "activo": True,
                },
            )
            productos.append(prod)
        self.stdout.write(self.style.SUCCESS("OK: 20 Productos listos."))

        # 3. Clientes (20)
        nombres_clientes = [
            ("Consorcio Edificio Alvear", "30-71452381-4", "Av. Libertador 1240"),
            ("Clínica San Lucas", "30-68912445-8", "Calle 14 N° 580"),
            ("Gimnasio Sport Center", "27-32114589-4", "Av. Santa Fe 3420"),
            ("Colegio Belgrano Day", "30-54210984-2", "Juramento 2100"),
            ("Restaurante El Establo", "30-70982314-9", "Costanera Norte 450"),
            ("Hotel Boutique del Parque", "30-71120934-1", "Juncal 1890"),
            ("Lavandería Sol y Luna", "20-28945612-3", "Rivadavia 8740"),
            ("Oficinas Torre Bouchard", "30-65498712-6", "Bouchard 547"),
            ("Jardín Maternal Rayito", "27-29451203-7", "Billinghurst 1120"),
            ("Estación de Servicio Shell Centro", "30-71889922-5", "Av. Córdoba 4500"),
            ("Taller Mecánico Los Primos", "20-25412987-9", "Warnes 1230"),
            ("Supermercado Familiar La Unión", "30-70881234-8", "Av. San Martín 2300"),
            ("Club Social y Deportivo Mitre", "30-52119934-2", "Pueyrredón 650"),
            ("Empresa de Limpieza Integral Norte", "30-71556677-1", "Panamericana Km 38"),
            ("Cafetería & Bistro Nueve", "20-33412589-1", "Palermo Soho 142"),
            ("Centro Médico Diagnóstico", "30-69874521-4", "Callao 890"),
            ("Residencia Geriátrica Los Abuelos", "30-64112233-9", "Cabildo 3100"),
            ("Industrias Metalúrgicas Sur", "30-58994411-7", "Parque Industrial Berazategui"),
            ("Peluquería & Spa Unisex", "27-35661245-8", "Corrientes 2450"),
            ("Teatro Municipal San Martín", "30-99881122-3", "Av. Corrientes 1530"),
        ]

        clientes = []
        for i, (nombre, doc, dom) in enumerate(nombres_clientes, 1):
            numero = doc.replace("-", "")
            cli, _ = Cliente.objects.get_or_create(
                numero_documento=numero,
                defaults={
                    "nombre": nombre,
                    "tipo_documento": "CUIT" if doc.startswith("30") else "DNI",
                    "domicilio": dom,
                    "correo": f"contacto{i}@empresa{i}.com.ar",
                    "telefono": f"11-4589-{1000 + i}",
                    "activo": True,
                },
            )
            clientes.append(cli)
        self.stdout.write(self.style.SUCCESS("OK: 20 Clientes listos."))

        # 4. Proveedores (20)
        nombres_proveedores = [
            ("Química del Plata S.A.", "30-61223344-9", "Av. Industrial 500"),
            ("Distribuidora Papelera Austral", "30-70112233-4", "Camino de Cintura 4500"),
            ("Plásticos Industriales Lanús", "30-58221144-6", "Hipólito Yrigoyen 2300"),
            ("Aromas & Fragancias de Argentina", "30-69332211-8", "Ruta 8 Km 54"),
            ("Laboratorios CleanTech S.R.L.", "30-71225588-1", "Parque Ind. Pilar"),
            ("Fábrica de Cepillos y Escobas Norte", "30-55443322-7", "Av. Mitre 3400"),
            ("Soluciones Químicas Integrales", "30-67889900-3", "Montes de Oca 1200"),
            ("Importadora de Guantes LatexPro", "30-71004455-2", "Av. Belgrano 980"),
            ("Empaques y Polietileno Sur", "30-62117788-5", "Florencio Varela 780"),
            ("Sulfatos y Clorados San Juan", "30-53441122-0", "Acceso Sur 1400"),
            ("Química Textil de Berazategui", "30-70559911-3", "Calle 148 N° 2100"),
            ("Inyectora Plástica San Fernando", "30-64778811-9", "Av. del Libertador 4100"),
            ("Papelera Institucional Zárate", "30-71336699-5", "Ruta 9 Km 88"),
            ("Aerosoles & Envases Quilmes", "30-59114477-2", "Andrés Baranda 600"),
            ("Fibras Sintéticas Argentina", "30-66225511-8", "Av. Calchaquí 1800"),
            ("Detergentes Concentrados San Justo", "30-70884433-1", "Arieta 2900"),
            ("Bioquímica Ambiental S.A.", "30-68441199-4", "Lavalle 1420"),
            ("Metalúrgica Manijas y Secadores", "30-57118833-6", "Perito Moreno 340"),
            ("Distribuidora Mayorista El Trébol", "30-71448822-7", "Ruta 3 Km 29"),
            ("Química Verde EcoClean", "30-63991144-5", "Av. San Martín 890"),
        ]

        proveedores = []
        for i, (nombre, doc, dom) in enumerate(nombres_proveedores, 1):
            numero = doc.replace("-", "")
            prov, _ = Proveedor.objects.get_or_create(
                numero_documento=numero,
                defaults={
                    "nombre": nombre,
                    "tipo_documento": "CUIT",
                    "domicilio": dom,
                    "correo": f"ventas@prov{i}.com.ar",
                    "telefono": f"11-4820-{2000 + i}",
                    "activo": True,
                },
            )
            proveedores.append(prov)
        self.stdout.write(self.style.SUCCESS("OK: 20 Proveedores listos."))

        # 5. Órdenes de compra (20 con sus ítems)
        estados_oc = ["RECIBIDA", "RECIBIDA", "PENDIENTE", "CANCELADA"]
        for i in range(1, 21):
            num_oc = f"OC-2026-{str(i).zfill(4)}"
            estado = estados_oc[i % len(estados_oc)]
            prov = proveedores[i - 1]

            oc, created = OrdenCompra.objects.get_or_create(
                numero_operacion=num_oc,
                defaults={
                    "proveedor": prov,
                    "estado": estado,
                    "observacion": f"Orden de compra semanal #{i} a {prov.nombre}",
                    "fecha": timezone.now(),
                },
            )

            if created:
                p1 = productos[(i * 2) % len(productos)]
                p2 = productos[(i * 2 + 1) % len(productos)]
                cant1 = random.randint(20, 60)
                cant2 = random.randint(15, 40)
                costo1 = (p1.precio_unitario * Decimal("0.65")).quantize(Decimal("0.01"))
                costo2 = (p2.precio_unitario * Decimal("0.65")).quantize(Decimal("0.01"))

                OrdenCompraItem.objects.create(
                    orden_compra=oc,
                    producto=p1,
                    producto_nombre=p1.nombre,
                    cantidad=cant1,
                    precio_unitario_compra=costo1,
                )
                OrdenCompraItem.objects.create(
                    orden_compra=oc,
                    producto=p2,
                    producto_nombre=p2.nombre,
                    cantidad=cant2,
                    precio_unitario_compra=costo2,
                )

        self.stdout.write(self.style.SUCCESS("OK: 20 Ordenes de Compra con items listas."))

        # 6. Pedidos / ventas (20 con sus ítems)
        estados_pedidos = ["CONFIRMADO", "CONFIRMADO", "PENDIENTE", "CANCELADO"]
        for i in range(1, 21):
            num_pedido = f"2026-{str(i).zfill(4)}"
            estado = estados_pedidos[i % len(estados_pedidos)]
            cli = clientes[i - 1]

            pedido, created = Pedido.objects.get_or_create(
                numero_operacion=num_pedido,
                defaults={
                    "cliente": cli,
                    "cliente_nombre": cli.nombre,
                    "cliente_tipo_documento": cli.tipo_documento or "",
                    "cliente_numero_documento": cli.numero_documento or "",
                    "cliente_telefono": cli.telefono or "",
                    "estado": estado,
                    "observacion": f"Venta institucional entregada a {cli.nombre}",
                    "fecha": timezone.now(),
                },
            )

            if created:
                prod_a = productos[(i * 3) % len(productos)]
                prod_b = productos[(i * 3 + 1) % len(productos)]
                cant_a = random.randint(2, 10)
                cant_b = random.randint(1, 6)

                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=prod_a,
                    producto_nombre=prod_a.nombre,
                    cantidad=cant_a,
                    precio_unitario=prod_a.precio_unitario,
                )
                PedidoItem.objects.create(
                    pedido=pedido,
                    producto=prod_b,
                    producto_nombre=prod_b.nombre,
                    cantidad=cant_b,
                    precio_unitario=prod_b.precio_unitario,
                )

        self.stdout.write(self.style.SUCCESS("OK: 20 Ventas / Pedidos con items listos."))
        self.stdout.write(self.style.SUCCESS("\nBase de datos cargada exitosamente para la demo!"))
