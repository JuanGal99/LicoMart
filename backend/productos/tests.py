from datetime import date

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from pedidos.models import DetallePedido, Pedidos
from usuarios.models import Usuarios

from .management.commands.cargar_productos_demo import PRODUCTOS_DEMO
from .models import Categoria, Productos


class CargarProductosDemoTests(TestCase):
    def test_command_is_idempotent(self):
        call_command("cargar_productos_demo")
        call_command("cargar_productos_demo")

        self.assertEqual(Productos.objects.count(), 18)
        self.assertEqual(
            Productos.objects.values("imagen").distinct().count(),
            18,
        )

    def test_command_does_not_overwrite_existing_products(self):
        categoria, _ = Categoria.objects.get_or_create(
            nombre="Otros licores",
            slug="otros-licores",
        )
        producto = Productos.objects.create(
            nombre=PRODUCTOS_DEMO[0]["nombre"],
            marca="Marca preexistente",
            categoria=categoria,
            descripcion="Descripción preexistente",
            stock=3,
            precio=12345,
            imagen=None,
        )

        call_command("cargar_productos_demo")

        producto.refresh_from_db()
        self.assertEqual(Productos.objects.count(), 18)
        self.assertEqual(producto.marca, "Marca preexistente")
        self.assertEqual(producto.descripcion, "Descripción preexistente")
        self.assertEqual(producto.stock, 3)
        self.assertEqual(producto.precio, 12345)
        self.assertIsNone(producto.imagen)
        self.assertEqual(producto.categoria, categoria)

    def test_explicit_refresh_only_changes_demo_metadata_and_is_idempotent(self):
        categoria, _ = Categoria.objects.get_or_create(
            nombre="Whisky",
            slug="whisky",
        )
        producto = Productos.objects.create(
            nombre=PRODUCTOS_DEMO[0]["nombre_anterior"],
            marca="",
            categoria=categoria,
            descripcion="Descripción anterior",
            stock=5,
            precio=12000,
        )

        call_command("cargar_productos_demo", "--actualizar-productos-demo-existentes")
        call_command("cargar_productos_demo", "--actualizar-productos-demo-existentes")

        producto.refresh_from_db()
        self.assertEqual(Productos.objects.count(), 18)
        self.assertEqual(producto.nombre, PRODUCTOS_DEMO[0]["nombre"])
        self.assertEqual(producto.marca, "Black & White")
        self.assertEqual(producto.stock, 5)
        self.assertEqual(producto.precio, 12000)
        self.assertEqual(
            producto.imagen,
            PRODUCTOS_DEMO[0]["imagen"],
        )

    def test_explicit_refresh_preserves_name_and_description_when_ordered(self):
        categoria, _ = Categoria.objects.get_or_create(
            nombre="Whisky",
            slug="whisky",
        )
        producto = Productos.objects.create(
            nombre=PRODUCTOS_DEMO[2]["nombre_anterior"],
            marca="Niebla Alta",
            categoria=categoria,
            descripcion="Descripción que conserva el pedido",
            stock=5,
            precio=12000,
        )
        usuario = Usuarios.objects.create(
            nombre="cliente-demo",
            email="cliente-demo@example.test",
            contraseña="hash-no-usado",
        )
        pedido = Pedidos.objects.create(
            id_usuario=usuario,
            fecha=date.today(),
        )
        detalle = DetallePedido.objects.create(
            id_pedido=pedido,
            id_producto=producto,
            cantidad=1,
        )

        call_command("cargar_productos_demo", "--actualizar-productos-demo-existentes")

        producto.refresh_from_db()
        detalle.refresh_from_db()
        self.assertEqual(producto.nombre, PRODUCTOS_DEMO[2]["nombre_anterior"])
        self.assertEqual(producto.descripcion, "Descripción que conserva el pedido")
        self.assertEqual(producto.marca, "Niebla Alta")
        self.assertEqual(producto.stock, 5)
        self.assertEqual(producto.precio, 12000)
        self.assertEqual(detalle.id_producto_id, producto.id)


class CatalogoProductosTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.whisky, _ = Categoria.objects.get_or_create(
            nombre="Whisky",
            slug="whisky",
        )
        cls.vinos, _ = Categoria.objects.get_or_create(
            nombre="Vinos",
            slug="vinos",
        )
        cls.productos = [
            Productos.objects.create(
                nombre="Roble Reserva",
                marca="Destilería Sierra",
                categoria=cls.whisky,
                descripcion="Whisky añejado",
                stock=12,
                precio=50000,
            ),
            Productos.objects.create(
                nombre="Malta Dorada",
                marca="Casa del Valle",
                categoria=cls.whisky,
                descripcion="Whisky de malta",
                stock=8,
                precio=90000,
            ),
            Productos.objects.create(
                nombre="Tinto de la Sierra",
                marca="Viña Clara",
                categoria=cls.vinos,
                descripcion="Vino tinto",
                stock=20,
                precio=35000,
            ),
        ]

    def get_resultados(self, query=""):
        response = self.client.get(reverse("lista_productos"), query)
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_api_includes_category_and_brand(self):
        data = self.get_resultados()

        self.assertEqual(data["total"], 3)
        self.assertEqual(len(data["categorias"]), 8)
        self.assertEqual(data["productos"][0]["marca"], "Destilería Sierra")
        self.assertEqual(data["productos"][0]["categoria"]["slug"], "whisky")

    def test_category_filter(self):
        data = self.get_resultados({"categoria": "whisky"})

        self.assertEqual(data["total"], 2)
        self.assertTrue(
            all(item["categoria"]["slug"] == "whisky" for item in data["productos"])
        )

    def test_price_range_filter(self):
        data = self.get_resultados({"precio_min": "40000", "precio_max": "60000"})

        self.assertEqual([item["nombre"] for item in data["productos"]], ["Roble Reserva"])

    def test_search_matches_brand_and_product_name(self):
        by_brand = self.get_resultados({"q": "casa del valle"})
        by_name = self.get_resultados({"q": "tinto"})

        self.assertEqual([item["nombre"] for item in by_brand["productos"]], ["Malta Dorada"])
        self.assertEqual([item["nombre"] for item in by_name["productos"]], ["Tinto de la Sierra"])

    def test_sorting(self):
        ascending = self.get_resultados({"orden": "precio_asc"})
        descending = self.get_resultados({"orden": "precio_desc"})
        alphabetical = self.get_resultados({"orden": "nombre_asc"})

        self.assertEqual(ascending["productos"][0]["precio"], 35000)
        self.assertEqual(descending["productos"][0]["precio"], 90000)
        self.assertEqual(alphabetical["productos"][0]["nombre"], "Malta Dorada")

    def test_filters_can_be_combined(self):
        data = self.get_resultados(
            {
                "categoria": "whisky",
                "precio_min": "40000",
                "precio_max": "100000",
                "q": "destilería",
                "orden": "precio_desc",
            }
        )

        self.assertEqual(data["total"], 1)
        self.assertEqual(data["productos"][0]["nombre"], "Roble Reserva")

    def test_invalid_price_range_returns_bad_request(self):
        response = self.client.get(
            reverse("lista_productos"),
            {"precio_min": "100", "precio_max": "50"},
        )

        self.assertEqual(response.status_code, 400)

    def test_product_can_still_be_added_to_cart(self):
        producto = self.productos[0]
        response = self.client.post(
            reverse("agregar_al_carrito", args=[producto.id]),
            data='{"cantidad": 1}',
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["success"])
        self.assertEqual(response.json()["carrito"][str(producto.id)]["cantidad"], 1)
