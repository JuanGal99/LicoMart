from django.conf import settings
from django.db import models
from productos.models import Productos
from usuarios.models import Usuarios
from django.utils import timezone

# Create your models here.

class Pedidos(models.Model):
    ESTADOS = [
        ('Pendiente', 'Pendiente'),
        ('En Proceso', 'En Proceso'),
        ('Completado', 'Completado'),
        ('Cancelado', 'Cancelado'),
    ]

    id_usuario = models.ForeignKey(Usuarios, on_delete=models.CASCADE, related_name='pedidos')
    fecha = models.DateField()
    estado = models.CharField(max_length=50, choices=ESTADOS, default='Pendiente')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    pago_confirmado = models.BooleanField(default=False)
    fecha_pago = models.DateTimeField(null=True, blank=True)
    referencia_demo = models.CharField(max_length=80, unique=True, null=True, blank=True)

    def __str__(self):
        return f"Pedido {self.id} de {self.id_usuario.nombre}"



class DetallePedido(models.Model):
    id_pedido = models.ForeignKey(Pedidos, on_delete=models.CASCADE, related_name='detalles')
    id_producto = models.ForeignKey(Productos, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    subtotal = models.FloatField(editable=False)
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.precio_unitario = self.id_producto.precio
        self.subtotal = self.cantidad * float(self.precio_unitario)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Detalle del Pedido {self.id_pedido.id} - Producto {self.id_producto.nombre}"


class MovimientoInventario(models.Model):
    TIPOS = [
        ("entrada", "Entrada"),
        ("salida", "Salida"),
        ("ajuste", "Ajuste"),
    ]

    producto = models.ForeignKey(
        Productos, on_delete=models.PROTECT, related_name="movimientos_inventario"
    )
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.PositiveIntegerField()
    stock_anterior = models.PositiveIntegerField()
    stock_nuevo = models.PositiveIntegerField()
    motivo = models.CharField(max_length=200)
    fecha = models.DateTimeField(default=timezone.now)
    responsable = models.ForeignKey(
        Usuarios, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="movimientos_inventario",
    )
    clave_idempotencia = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()} {self.cantidad} x {self.producto.nombre}"


class MovimientoFinanciero(models.Model):
    TIPOS = [
        ("ingreso", "Ingreso"),
        ("egreso", "Egreso"),
    ]

    tipo = models.CharField(max_length=10, choices=TIPOS)
    concepto = models.CharField(max_length=160)
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    fecha = models.DateField(default=timezone.localdate)
    observaciones = models.CharField(max_length=500, blank=True)
    pedido = models.OneToOneField(
        Pedidos, on_delete=models.PROTECT, null=True, blank=True,
        related_name="movimiento_financiero",
    )
    responsable = models.ForeignKey(
        Usuarios, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="movimientos_financieros",
    )
    es_demo = models.BooleanField(default=False)
    clave_idempotencia = models.CharField(max_length=100, unique=True, null=True, blank=True)

    class Meta:
        ordering = ["-fecha", "-id"]

    def __str__(self):
        return f"{self.get_tipo_display()}: {self.concepto} ({self.importe})"