import json
import os
from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.management import call_command
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from pedidos.models import (
    DetallePedido,
    MovimientoFinanciero,
    MovimientoInventario,
    Pedidos,
)
from productos.models import Categoria, Productos
from usuarios.models import Usuarios


class AdminStoreTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.category = Categoria.objects.get(slug="whisky")
        cls.product = Productos.objects.create(
            nombre="Whisky de prueba",
            marca="Bodega Demo",
            categoria=cls.category,
            stock=20,
            precio=50000,
        )
        cls.admin = Usuarios.objects.create(
            nombre="admin-pruebas",
            email="admin-pruebas@example.test",
            contraseña="!",
            rol="admin",
        )
        cls.customer = Usuarios.objects.create(
            nombre="cliente-pruebas",
            email="cliente-pruebas@example.test",
            contraseña="!",
            rol="usuario",
        )

    def admin_client(self):
        client = Client()
        session = client.session
        session["usuario_id"] = self.admin.id
        session.save()
        return client

    def create_order(self, *, status="Pendiente", paid=False, quantity=2):
        order = Pedidos.objects.create(
            id_usuario=self.customer,
            fecha=date.today(),
            estado=status,
            pago_confirmado=paid,
        )
        DetallePedido.objects.create(
            id_pedido=order,
            id_producto=self.product,
            cantidad=quantity,
            precio_unitario=Decimal("50000.00"),
        )
        order.total = Decimal("50000.00") * quantity
        order.save(update_fields=["total"])
        return order

    def test_dashboard_and_product_endpoints_require_admin_role(self):
        url = reverse("admin_dashboard")
        self.assertEqual(self.client.get(url).status_code, 401)

        user_client = Client()
        session = user_client.session
        session["usuario_id"] = self.customer.id
        session.save()
        self.assertEqual(user_client.get(url).status_code, 403)

        response = self.admin_client().get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["kpis"]["productos"], 1)

    def test_admin_write_endpoints_enforce_csrf_tokens(self):
        client = Client(enforce_csrf_checks=True)
        session = client.session
        session["usuario_id"] = self.admin.id
        session.save()
        payload = json.dumps({
            "tipo": "egreso",
            "concepto": "Prueba CSRF",
            "importe": 1000,
            "fecha": date.today().isoformat(),
        })
        url = reverse("admin_finanzas")
        denied = client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="csrf-test",
        )
        self.assertEqual(denied.status_code, 403)

        client.get(reverse("csrf_token"))
        token = client.cookies["csrftoken"].value
        allowed = client.post(
            url,
            data=payload,
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="csrf-test",
            HTTP_X_CSRFTOKEN=token,
        )
        self.assertEqual(allowed.status_code, 201)

    def test_product_creation_validation_and_safe_deletion(self):
        client = self.admin_client()
        payload = {
            "nombre": "Ginebra nueva",
            "marca": "Botánica",
            "descripcion": "Prueba de CRUD",
            "categoria_id": self.category.id,
            "precio": 74000,
            "stock": 7,
            "imagen": "https://example.test/ginebra.jpg",
        }
        response = client.post(
            reverse("admin_productos"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        product_id = response.json()["producto"]["id"]
        product = Productos.objects.get(pk=product_id)
        self.assertEqual(product.stock, 7)
        self.assertEqual(product.movimientos_inventario.count(), 1)

        self.create_order()
        response = client.delete(reverse("admin_producto", args=[self.product.id]))
        self.assertEqual(response.status_code, 409)

    def test_inventory_adjustments_are_validated_and_idempotent(self):
        client = self.admin_client()
        url = reverse("admin_inventario")
        payload = {
            "producto_id": self.product.id,
            "tipo": "salida",
            "cantidad": 3,
            "motivo": "Conteo físico",
        }
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="stock-test-1",
        )
        self.assertEqual(response.status_code, 201)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 17)

        repeated = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="stock-test-1",
        )
        self.assertTrue(repeated.json()["repetido"])
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 17)

        payload["cantidad"] = 18
        response = client.post(
            url,
            data=json.dumps(payload),
            content_type="application/json",
            HTTP_IDEMPOTENCY_KEY="stock-test-negative",
        )
        self.assertEqual(response.status_code, 400)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 17)

    def test_checkout_uses_server_price_and_records_stock_snapshot(self):
        client = Client()
        session = client.session
        session["usuario_id"] = self.customer.id
        session["carrito"] = {
            str(self.product.id): {
                "nombre": self.product.nombre,
                "precio": 1,
                "cantidad": 2,
            }
        }
        session.save()

        response = client.post(reverse("confirmar_compra"))
        self.assertEqual(response.status_code, 200)
        order = Pedidos.objects.get(pk=response.json()["pedido_id"])
        detail = order.detalles.get()
        self.assertEqual(detail.precio_unitario, Decimal("50000.00"))
        self.assertEqual(order.total, Decimal("100000.00"))
        self.assertFalse(order.pago_confirmado)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 18)
        self.assertEqual(MovimientoInventario.objects.filter(
            clave_idempotencia__startswith=f"pedido:{order.id}:reserva:"
        ).count(), 1)

        self.product.precio = 80000
        self.product.save(update_fields=["precio"])
        detail.refresh_from_db()
        self.assertEqual(detail.precio_unitario, Decimal("50000.00"))

    def test_confirming_payment_creates_one_income_and_does_not_discount_stock_again(self):
        order = self.create_order()
        client = self.admin_client()
        url = reverse("admin_confirmar_pago", args=[order.id])
        first = client.post(url)
        second = client.post(url)

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertTrue(order.pago_confirmado)
        self.assertEqual(order.estado, "Completado")
        self.assertEqual(order.total, Decimal("100000.00"))
        self.assertEqual(self.product.stock, 20)
        self.assertEqual(MovimientoFinanciero.objects.filter(pedido=order).count(), 1)

    def test_canceled_order_is_not_income_and_cannot_be_paid(self):
        order = self.create_order()
        self.product.stock -= 2
        self.product.save(update_fields=["stock"])
        client = self.admin_client()

        response = client.patch(
            reverse("admin_actualizar_pedido", args=[order.id]),
            data='{"estado":"Cancelado"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 20)
        self.assertEqual(MovimientoInventario.objects.filter(
            clave_idempotencia=f"pedido:{order.id}:cancelacion:{self.product.id}"
        ).count(), 1)

        payment = client.post(reverse("admin_confirmar_pago", args=[order.id]))
        self.assertEqual(payment.status_code, 409)
        self.assertFalse(MovimientoFinanciero.objects.filter(pedido=order).exists())

    @override_settings(DEBUG=True)
    def test_demo_seed_is_idempotent_and_records_balanced_sales(self):
        with patch.dict(os.environ, {"ALLOW_DEMO_ADMIN": "true"}):
            call_command("cargar_datos_demo", verbosity=0)
            first_counts = (
                Pedidos.objects.filter(referencia_demo__isnull=False).count(),
                MovimientoFinanciero.objects.filter(es_demo=True).count(),
                MovimientoInventario.objects.filter(
                    clave_idempotencia__startswith="demo:"
                ).count(),
            )
            call_command("cargar_datos_demo", verbosity=0)
        second_counts = (
            Pedidos.objects.filter(referencia_demo__isnull=False).count(),
            MovimientoFinanciero.objects.filter(es_demo=True).count(),
            MovimientoInventario.objects.filter(
                clave_idempotencia__startswith="demo:"
            ).count(),
        )
        self.assertEqual(first_counts, second_counts)
        self.assertEqual(first_counts[0], 12)
        self.assertGreater(MovimientoFinanciero.objects.filter(tipo="ingreso", es_demo=True).count(), 0)
        self.assertGreater(MovimientoFinanciero.objects.filter(tipo="egreso", es_demo=True).count(), 0)
        self.assertTrue(Productos.objects.filter(stock__lte=5).exists())
