from decimal import Decimal

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


def guardar_precios_historicos(apps, schema_editor):
    DetallePedido = apps.get_model("pedidos", "DetallePedido")
    Pedidos = apps.get_model("pedidos", "Pedidos")
    alias = schema_editor.connection.alias

    for detalle in DetallePedido.objects.using(alias).all().iterator():
        if detalle.cantidad:
            precio = Decimal(str(detalle.subtotal)) / Decimal(detalle.cantidad)
        else:
            precio = Decimal("0")
        DetallePedido.objects.using(alias).filter(pk=detalle.pk).update(
            precio_unitario=precio.quantize(Decimal("0.01"))
        )

    for pedido in Pedidos.objects.using(alias).all().iterator():
        total = sum(
            (
                Decimal(str(detalle.subtotal))
                for detalle in DetallePedido.objects.using(alias).filter(
                    id_pedido_id=pedido.pk
                )
            ),
            Decimal("0"),
        )
        Pedidos.objects.using(alias).filter(pk=pedido.pk).update(
            total=total.quantize(Decimal("0.01"))
        )


class Migration(migrations.Migration):
    dependencies = [
        ("productos", "0003_categoria_y_marca"),
        ("pedidos", "0001_initial"),
        ("usuarios", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="pedidos",
            name="total",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.AddField(
            model_name="pedidos",
            name="pago_confirmado",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="pedidos",
            name="fecha_pago",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="pedidos",
            name="referencia_demo",
            field=models.CharField(blank=True, max_length=80, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="detallepedido",
            name="precio_unitario",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=12),
        ),
        migrations.RunPython(guardar_precios_historicos, migrations.RunPython.noop),
        migrations.CreateModel(
            name="MovimientoInventario",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("entrada", "Entrada"),
                            ("salida", "Salida"),
                            ("ajuste", "Ajuste"),
                        ],
                        max_length=10,
                    ),
                ),
                ("cantidad", models.PositiveIntegerField()),
                ("stock_anterior", models.PositiveIntegerField()),
                ("stock_nuevo", models.PositiveIntegerField()),
                ("motivo", models.CharField(max_length=200)),
                ("fecha", models.DateTimeField(default=django.utils.timezone.now)),
                (
                    "clave_idempotencia",
                    models.CharField(blank=True, max_length=100, null=True, unique=True),
                ),
                (
                    "producto",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimientos_inventario",
                        to="productos.productos",
                    ),
                ),
                (
                    "responsable",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movimientos_inventario",
                        to="usuarios.usuarios",
                    ),
                ),
            ],
            options={"ordering": ["-fecha", "-id"]},
        ),
        migrations.CreateModel(
            name="MovimientoFinanciero",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[("ingreso", "Ingreso"), ("egreso", "Egreso")],
                        max_length=10,
                    ),
                ),
                ("concepto", models.CharField(max_length=160)),
                ("importe", models.DecimalField(decimal_places=2, max_digits=12)),
                ("fecha", models.DateField(default=django.utils.timezone.localdate)),
                ("observaciones", models.CharField(blank=True, max_length=500)),
                ("es_demo", models.BooleanField(default=False)),
                (
                    "clave_idempotencia",
                    models.CharField(blank=True, max_length=100, null=True, unique=True),
                ),
                (
                    "pedido",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="movimiento_financiero",
                        to="pedidos.pedidos",
                    ),
                ),
                (
                    "responsable",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="movimientos_financieros",
                        to="usuarios.usuarios",
                    ),
                ),
            ],
            options={"ordering": ["-fecha", "-id"]},
        ),
    ]
