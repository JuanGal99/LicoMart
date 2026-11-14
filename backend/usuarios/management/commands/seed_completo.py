import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction
from django.utils import timezone

from pedidos.models import (
    DetallePedido,
    MovimientoFinanciero,
    MovimientoInventario,
    Pedidos,
)
from productos.models import Categoria, Productos
from usuarios.models import Usuarios


CATEGORIAS = [
    ("Whisky", "whisky"),
    ("Ron", "ron"),
    ("Ginebra", "ginebra"),
    ("Vodka", "vodka"),
    ("Tequila", "tequila"),
    ("Vinos", "vinos"),
    ("Cervezas", "cervezas"),
    ("Otros licores", "otros-licores"),
]

PRODUCTOS = [
    # Whisky
    {"nombre": "Black & White Scotch Whisky", "marca": "Black & White", "categoria": "whisky",
     "descripcion": "Whisky escocés blended de perfil suave.", "stock": 45, "precio": 42900,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/41/Black_%26_White_%28whisky%29_bottle_01.jpg/960px-Black_%26_White_%28whisky%29_bottle_01.jpg"},
    {"nombre": "Scotch Malt Whisky Society Single Malt", "marca": "Scotch Malt Whisky Society", "categoria": "whisky",
     "descripcion": "Whisky escocés de malta en presentación de colección.", "stock": 28, "precio": 68500,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c9/Bottle_of_whisky_from_the_Scotch_Malt_Whisky_Society.jpg/960px-Bottle_of_whisky_from_the_Scotch_Malt_Whisky_Society.jpg"},
    {"nombre": "English Whisky Collection", "marca": "The English Whisky Co.", "categoria": "whisky",
     "descripcion": "Selección de whisky inglés de malta.", "stock": 15, "precio": 112000,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/a/a5/English_Whisky_bottles.webp/960px-English_Whisky_bottles.webp"},
    # Ron
    {"nombre": "Captain Morgan Rum", "marca": "Captain Morgan", "categoria": "ron",
     "descripcion": "Ron especiado de origen caribeño.", "stock": 52, "precio": 38900,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c2/Bottle_of_Captain_Morgan_Rum_01.jpg/960px-Bottle_of_Captain_Morgan_Rum_01.jpg"},
    {"nombre": "Ron Zacapa XO", "marca": "Zacapa", "categoria": "ron",
     "descripcion": "Ron guatemalteco de reserva extra añeja.", "stock": 20, "precio": 59700,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/7/76/Ron-Zacapa-XO.jpg/960px-Ron-Zacapa-XO.jpg"},
    {"nombre": "Diplomático Reserva Exclusiva", "marca": "Diplomático", "categoria": "ron",
     "descripcion": "Ron venezolano premium con notas de caramelo y cacao.", "stock": 18, "precio": 75000,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/2a/Diplomatico_Reserva_Exclusiva.jpg/400px-Diplomatico_Reserva_Exclusiva.jpg"},
    # Ginebra
    {"nombre": "Hendrick's Gin", "marca": "Hendrick's", "categoria": "ginebra",
     "descripcion": "Ginebra escocesa con notas de pepino y rosa.", "stock": 33, "precio": 52900,
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/9/9c/Hendrick%27s_Gin_-_Bottle.png"},
    {"nombre": "Gordon's London Dry Gin", "marca": "Gordon's", "categoria": "ginebra",
     "descripcion": "Ginebra London Dry de perfil clásico y enebro.", "stock": 25, "precio": 63400,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/8/87/Vintage_Gordon%E2%80%99s_Gin_bottle.jpg/960px-Vintage_Gordon%E2%80%99s_Gin_bottle.jpg"},
    # Vodka
    {"nombre": "Crystal Head Vodka", "marca": "Crystal Head", "categoria": "vodka",
     "descripcion": "Vodka canadiense en su característica botella de cristal.", "stock": 40, "precio": 31500,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/5/54/Crystal_Head_Vodka.jpg/960px-Crystal_Head_Vodka.jpg"},
    {"nombre": "Tito's Handmade Vodka 1.75L", "marca": "Tito's", "categoria": "vodka",
     "descripcion": "Vodka artesanal de maíz en presentación de 1.75 litros.", "stock": 30, "precio": 47800,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/3/30/Tito%27s_Vodka_bottle_1.75L_size.jpg/960px-Tito%27s_Vodka_bottle_1.75L_size.jpg"},
    # Tequila
    {"nombre": "Tequila Corralejo Blanco 100ml", "marca": "Corralejo", "categoria": "tequila",
     "descripcion": "Tequila blanco de agave azul en botella de 100 ml.", "stock": 35, "precio": 55400,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/e/e8/Tequila_Corralejo_100ml_%28Blanco%29%2C_Mexico%2C_2026-03-30.jpg/960px-Tequila_Corralejo_100ml_%28Blanco%29%2C_Mexico%2C_2026-03-30.jpg"},
    {"nombre": "Tequila Corralejo Reposado 100ml", "marca": "Corralejo", "categoria": "tequila",
     "descripcion": "Tequila reposado en barrica en botella de 100 ml.", "stock": 22, "precio": 72900,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/4/47/Tequila_Corralejo_100ml_%28Reposado%29%2C_Mexico%2C_2026-03-30.jpg/960px-Tequila_Corralejo_100ml_%28Reposado%29%2C_Mexico%2C_2026-03-30.jpg"},
    # Vinos
    {"nombre": "Barefoot White Zinfandel", "marca": "Barefoot", "categoria": "vinos",
     "descripcion": "Vino rosado White Zinfandel de perfil frutal.", "stock": 50, "precio": 36200,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f9/Bottle_and_glass_of_Barefoot_white_zinfandel_wine%2C_2012.jpg/960px-Bottle_and_glass_of_Barefoot_white_zinfandel_wine%2C_2012.jpg"},
    {"nombre": "Tsimlyansk Red Wine", "marca": "Tsimlyansk", "categoria": "vinos",
     "descripcion": "Vino tinto de la región vinícola de Tsimlyansk.", "stock": 38, "precio": 33800,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/b/b8/Tsimlyansk_wines%2C_Rostov-on-Don%2C_Russia.jpg/960px-Tsimlyansk_wines%2C_Rostov-on-Don%2C_Russia.jpg"},
    {"nombre": "Tsimlyansk Wine Collection", "marca": "Tsimlyansk", "categoria": "vinos",
     "descripcion": "Selección de vinos de la región de Tsimlyansk.", "stock": 27, "precio": 34700,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/9a/Tsimlyansk_wines%2C_Wine_bottles%2C_Rostov-on-Don%2C_Russia.jpg/960px-Tsimlyansk_wines%2C_Wine_bottles%2C_Rostov-on-Don%2C_Russia.jpg"},
    # Cervezas
    {"nombre": "Angkor Premium Beer", "marca": "Angkor", "categoria": "cervezas",
     "descripcion": "Cerveza lager camboyana de sabor equilibrado.", "stock": 60, "precio": 8900,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/9/99/Angkor_beer_bottle_%26_glass.jpg/960px-Angkor_beer_bottle_%26_glass.jpg"},
    {"nombre": "Grolsch Premium Lager", "marca": "Grolsch", "categoria": "cervezas",
     "descripcion": "Cerveza lager neerlandesa de fermentación baja.", "stock": 55, "precio": 7900,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/2/20/Grolsch_Beer_Bottles.jpg/960px-Grolsch_Beer_Bottles.jpg"},
    # Otros licores
    {"nombre": "Cointreau Orange Liqueur", "marca": "Cointreau", "categoria": "otros-licores",
     "descripcion": "Licor de naranja francés para coctelería y sobremesa.", "stock": 22, "precio": 61900,
     "imagen": "https://upload.wikimedia.org/wikipedia/commons/b/b6/Cointreau.jpg"},
    {"nombre": "Baileys Original Irish Cream", "marca": "Baileys", "categoria": "otros-licores",
     "descripcion": "Licor de crema irlandesa con whiskey.", "stock": 19, "precio": 41800,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/0/0d/Baileys_Original_Irish_Cream_Bottle.jpg/960px-Baileys_Original_Irish_Cream_Bottle.jpg"},
    {"nombre": "Jägermeister", "marca": "Jägermeister", "categoria": "otros-licores",
     "descripcion": "Licor de hierbas alemán con 56 ingredientes botánicos.", "stock": 30, "precio": 45500,
     "imagen": "https://thumb.wikimedia.org/wikipedia/commons/thumb/c/c0/Jagermeister_bottle.jpg/400px-Jagermeister_bottle.jpg"},
]

USUARIOS = [
    {"nombre": "admin", "email": "admin@licomart.com", "password": "Admin2026!", "rol": "admin"},
    {"nombre": "usuario", "email": "usuario@licomart.com", "password": "Usuario2026!", "rol": "usuario"},
]

PEDIDOS_DEMO = [
    ("Completado", True, 2, 0),
    ("Completado", True, 3, 2),
    ("Completado", True, 1, 4),
    ("Completado", True, 2, 6),
    ("Completado", True, 1, 8),
    ("Completado", True, 3, 10),
    ("Completado", True, 2, 13),
    ("Completado", True, 1, 16),
    ("En Proceso", False, 2, 1),
    ("En Proceso", False, 1, 0),
    ("Pendiente", False, 1, 0),
    ("Pendiente", False, 2, 0),
    ("Cancelado", False, 1, 5),
]

EGRESOS_DEMO = [
    ("Compra de inventario mayorista", "Reposición de stock mes de noviembre", 420000, 25),
    ("Transporte de mercancía", "Flete desde bodega central", 38000, 20),
    ("Gastos operativos tienda", "Servicios públicos, limpieza y mantenimiento", 62500, 15),
    ("Compra de envases y empaques", "Bolsas, cajas y material de empaque", 29500, 8),
    ("Publicidad digital", "Campaña en redes sociales", 85000, 3),
]


class Command(BaseCommand):
    help = "Borra TODOS los datos y recrea usuarios, productos, pedidos, inventario y finanzas de demostración."

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("Este comando solo se permite con DEBUG=true.")

        self.stdout.write(self.style.WARNING("Borrando todos los datos..."))
        self._borrar_todo()

        self.stdout.write("Creando categorías...")
        categorias = {}
        for nombre, slug in CATEGORIAS:
            categorias[slug] = Categoria.objects.create(nombre=nombre, slug=slug)

        self.stdout.write("Creando usuarios...")
        usuarios = {}
        for u in USUARIOS:
            user = Usuarios(nombre=u["nombre"], email=u["email"], rol=u["rol"])
            user.set_password(u["password"])
            user.save()
            usuarios[u["rol"]] = user

        admin = usuarios["admin"]
        cliente = usuarios["usuario"]

        self.stdout.write("Creando productos...")
        productos = []
        for p in PRODUCTOS:
            producto = Productos.objects.create(
                nombre=p["nombre"],
                marca=p["marca"],
                descripcion=p["descripcion"],
                stock=p["stock"],
                precio=Decimal(str(p["precio"])),
                imagen=p["imagen"],
                categoria=categorias[p["categoria"]],
            )
            productos.append(producto)

        self.stdout.write("Registrando inventario inicial...")
        for producto in productos:
            MovimientoInventario.objects.create(
                producto=producto,
                tipo="entrada",
                cantidad=producto.stock,
                stock_anterior=0,
                stock_nuevo=producto.stock,
                motivo="Inventario inicial",
                responsable=admin,
                clave_idempotencia=f"seed:apertura:{producto.id}",
            )

        hoy = timezone.localdate()
        self.stdout.write("Creando pedidos y ventas...")
        for i, (estado, pagado, cantidad, dias_atras) in enumerate(PEDIDOS_DEMO):
            producto = productos[i % len(productos)]
            fecha = hoy - timedelta(days=dias_atras)

            with transaction.atomic():
                producto = Productos.objects.select_for_update().get(pk=producto.pk)

                if estado != "Cancelado" and producto.stock < cantidad:
                    continue

                pedido = Pedidos.objects.create(
                    id_usuario=cliente,
                    fecha=fecha,
                    estado=estado,
                    pago_confirmado=pagado,
                    fecha_pago=timezone.now() - timedelta(days=dias_atras) if pagado else None,
                    referencia_demo=f"LICOMART-{i + 1:04d}",
                )

                precio = producto.precio
                DetallePedido.objects.create(
                    id_pedido=pedido,
                    id_producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                )
                pedido.total = precio * cantidad
                pedido.save(update_fields=["total"])

                if estado != "Cancelado":
                    anterior = producto.stock
                    producto.stock -= cantidad
                    producto.save(update_fields=["stock"])
                    MovimientoInventario.objects.create(
                        producto=producto,
                        tipo="salida",
                        cantidad=cantidad,
                        stock_anterior=anterior,
                        stock_nuevo=producto.stock,
                        motivo=f"Venta pedido #{pedido.id}",
                        responsable=admin,
                        clave_idempotencia=f"seed:venta:{pedido.id}:{producto.id}",
                    )

                if pagado:
                    MovimientoFinanciero.objects.create(
                        tipo="ingreso",
                        concepto=f"Venta pedido #{pedido.id} — {producto.nombre}",
                        importe=pedido.total,
                        fecha=fecha,
                        observaciones=f"Pago confirmado del pedido #{pedido.id}.",
                        pedido=pedido,
                        responsable=admin,
                        es_demo=True,
                        clave_idempotencia=f"seed:ingreso:{pedido.id}",
                    )

        self.stdout.write("Creando egresos...")
        for concepto, obs, importe, dias_atras in EGRESOS_DEMO:
            MovimientoFinanciero.objects.create(
                tipo="egreso",
                concepto=concepto,
                importe=Decimal(importe),
                fecha=hoy - timedelta(days=dias_atras),
                observaciones=obs,
                responsable=admin,
                es_demo=True,
                clave_idempotencia=f"seed:egreso:{concepto}",
            )

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("=" * 56))
        self.stdout.write(self.style.SUCCESS("  SEED COMPLETADO — LicoMart listo para demostración"))
        self.stdout.write(self.style.SUCCESS("=" * 56))
        self.stdout.write("")
        self.stdout.write(f"  Productos:   {len(productos)}")
        self.stdout.write(f"  Pedidos:     {len(PEDIDOS_DEMO)}")
        self.stdout.write(f"  Categorías:  {len(CATEGORIAS)}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("  CREDENCIALES DE ACCESO"))
        self.stdout.write(self.style.SUCCESS("-" * 56))
        for u in USUARIOS:
            self.stdout.write(f"  Rol: {u['rol']:<10} Usuario: {u['nombre']:<12} Clave: {u['password']}")
        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(f"  URL: http://localhost:5173"))
        self.stdout.write(self.style.SUCCESS("=" * 56))
        self.stdout.write("")

    def _borrar_todo(self):
        MovimientoFinanciero.objects.all().delete()
        MovimientoInventario.objects.all().delete()
        DetallePedido.objects.all().delete()
        Pedidos.objects.all().delete()
        Productos.objects.all().delete()
        Categoria.objects.all().delete()
        Usuarios.objects.all().delete()
