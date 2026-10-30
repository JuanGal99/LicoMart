import os
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from pedidos.models import (
    DetallePedido,
    MovimientoFinanciero,
    MovimientoInventario,
    Pedidos,
)
from productos.management.commands.cargar_productos_demo import PRODUCTOS_DEMO
from productos.models import Productos
from usuarios.models import Usuarios


ESTADOS_DEMO = [
    ("Completado", True),
    ("Completado", True),
    ("Pendiente", False),
    ("Completado", True),
    ("Cancelado", False),
    ("Completado", True),
    ("En Proceso", False),
    ("Completado", True),
    ("Pendiente", False),
    ("Completado", True),
    ("Completado", True),
    ("Completado", True),
]

EGRESOS_DEMO = [
    ("Compra demo de mercancía", "Compra de inventario para demostración", 420000, 24),
    ("Transporte demo", "Traslado de mercancía ficticio", 38000, 18),
    ("Gastos operativos demo", "Materiales y operación de tienda demo", 62500, 12),
    ("Compra demo de envases", "Suministros de empaque ficticios", 29500, 5),
]


class Command(BaseCommand):
    help = "Carga productos, pedidos, ventas, movimientos y finanzas de demostración sin sobrescribir datos."

    def handle(self, *args, **options):
        if not settings.DEBUG or os.environ.get("ALLOW_DEMO_ADMIN") != "true":
            raise CommandError(
                "La carga demo solo se permite con DEBUG=true y ALLOW_DEMO_ADMIN=true."
            )

        call_command("crear_admin_demo")
        call_command("cargar_productos_demo")
        productos = []
        for item in PRODUCTOS_DEMO:
            producto = Productos.objects.filter(nombre=item["nombre"]).first()
            if producto is None:
                producto = Productos.objects.filter(nombre=item["nombre_anterior"]).first()
            if producto is None:
                raise CommandError(f"No se encontró el producto demo {item['nombre']}.")
            productos.append(producto)

        admin = Usuarios.objects.get(nombre="admin_demo")
        clientes = [self._obtener_cliente(index) for index in range(1, 5)]
        hoy = timezone.localdate()
        apertura_creada = 0
        for producto in productos:
            _, creado = MovimientoInventario.objects.get_or_create(
                clave_idempotencia=f"demo:apertura:{producto.id}",
                defaults={
                    "producto": producto,
                    "tipo": "ajuste",
                    "cantidad": producto.stock,
                    "stock_anterior": 0,
                    "stock_nuevo": producto.stock,
                    "motivo": "Existencia inicial reportada para demostración; no altera el stock.",
                    "responsable": admin,
                },
            )
            apertura_creada += int(creado)
        candidato_stock_bajo = min(
            (
                producto
                for index, producto in enumerate(productos)
                if index != 4 and producto.stock > 5
            ),
            key=lambda producto: producto.stock,
            default=None,
        )
        pedidos_creados = 0
        ingresos_creados = 0
        movimientos_creados = 0

        for index, (estado, pagado) in enumerate(ESTADOS_DEMO):
            referencia = f"LICOMART-DEMO-{index + 1:03d}"
            if Pedidos.objects.filter(referencia_demo=referencia).exists():
                continue
            producto = productos[index % len(productos)]
            with transaction.atomic():
                producto = Productos.objects.select_for_update().get(pk=producto.pk)
                cantidad = (
                    max(1, producto.stock - 4)
                    if candidato_stock_bajo and producto.pk == candidato_stock_bajo.pk
                    else 1 + index % 2
                )
                if estado != "Cancelado" and producto.stock < cantidad:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Se omitió {referencia}: stock insuficiente para {producto.nombre}."
                        )
                    )
                    continue
                fecha = hoy - timedelta(days=(index * 2) % 29)
                pedido = Pedidos.objects.create(
                    id_usuario=clientes[index % len(clientes)],
                    fecha=fecha,
                    estado=estado,
                    pago_confirmado=pagado,
                    fecha_pago=timezone.make_aware(
                        timezone.datetime.combine(fecha, timezone.datetime.min.time())
                    ) if pagado else None,
                    referencia_demo=referencia,
                )
                precio = Decimal(str(producto.precio)).quantize(Decimal("0.01"))
                DetallePedido.objects.create(
                    id_pedido=pedido,
                    id_producto=producto,
                    cantidad=cantidad,
                    precio_unitario=precio,
                )
                pedido.total = precio * cantidad
                pedido.save(update_fields=["total"])
                pedidos_creados += 1

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
                        motivo=f"Reserva de venta demo #{pedido.id}",
                        responsable=admin,
                        clave_idempotencia=f"demo:pedido:{referencia}:producto:{producto.id}",
                    )
                    movimientos_creados += 1

                if pagado:
                    MovimientoFinanciero.objects.create(
                        tipo="ingreso",
                        concepto=f"Venta demo pedido #{pedido.id}",
                        importe=pedido.total,
                        fecha=fecha,
                        observaciones="Ingreso vinculado a venta de demostración.",
                        pedido=pedido,
                        responsable=admin,
                        es_demo=True,
                        clave_idempotencia=f"demo:ingreso:{referencia}",
                    )
                    ingresos_creados += 1

        egresos_creados = 0
        for concepto, observaciones, importe, dias_atras in EGRESOS_DEMO:
            _, creado = MovimientoFinanciero.objects.get_or_create(
                clave_idempotencia=f"demo:egreso:{concepto}",
                defaults={
                    "tipo": "egreso",
                    "concepto": concepto,
                    "importe": Decimal(importe),
                    "fecha": hoy - timedelta(days=dias_atras),
                    "observaciones": observaciones,
                    "responsable": admin,
                    "es_demo": True,
                },
            )
            egresos_creados += int(creado)

        self.stdout.write(self.style.SUCCESS(
            "Carga demo completada: "
            f"{len(productos)} productos disponibles, {pedidos_creados} pedidos, "
            f"{ingresos_creados} ingresos, {egresos_creados} egresos, "
            f"{movimientos_creados + apertura_creada} movimientos nuevos."
        ))

    @staticmethod
    def _obtener_cliente(numero):
        email = f"cliente.demo.{numero}@licomart.local"
        nombre = f"cliente_demo_{numero}"
        usuario = Usuarios.objects.filter(email=email).first()
        if usuario:
            return usuario
        candidato = nombre
        sufijo = 1
        while Usuarios.objects.filter(nombre=candidato).exists():
            sufijo += 1
            candidato = f"{nombre}_{sufijo}"
        return Usuarios.objects.create(
            nombre=candidato,
            email=email,
            contraseña="!",
            rol="usuario",
        )
