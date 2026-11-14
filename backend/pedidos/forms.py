from django.forms import ModelForm, modelformset_factory, DateInput
from .models import Pedidos, DetallePedido



class PedidoForm(ModelForm):
    class Meta:
        model = Pedidos
        fields = ['id_usuario', 'fecha', 'estado']
        widgets = {
            'fecha': DateInput(attrs={'type': 'date'})
        }

class DetallePedidoForm(ModelForm):
    class Meta:
        model = DetallePedido
        exclude = ['subtotal']

DetallePedidoFormSet = modelformset_factory(
    DetallePedido,
    fields=['id_producto', 'cantidad'],
    extra=1,
)