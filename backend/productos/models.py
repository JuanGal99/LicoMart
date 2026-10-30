from django.db import models


class Categoria(models.Model):
    nombre = models.CharField(max_length=60, unique=True)
    slug = models.SlugField(max_length=60, unique=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name_plural = "categorías"

    def __str__(self):
        return self.nombre


class Productos(models.Model):
    nombre = models.CharField(max_length=100)
    marca = models.CharField(max_length=100, blank=True, default="")
    descripcion = models.CharField(max_length=200, blank=True, null=True)
    stock = models.IntegerField()
    precio = models.FloatField()
    imagen = models.URLField(max_length=500, blank=True, null=True)
    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.PROTECT,
        related_name="productos",
    )

    def __str__(self):
        return self.nombre
