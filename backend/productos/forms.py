from django.forms import ModelForm
from .models import Productos


class ProductoForm(ModelForm):
    class Meta:
        model = Productos
        fields = ['nombre', 'marca', 'categoria', 'descripcion', 'stock', 'precio', 'imagen']
