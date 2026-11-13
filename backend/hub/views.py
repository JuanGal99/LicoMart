from django.http import JsonResponse
from productos.models import Productos


def index(request):
    productos = Productos.objects.select_related("categoria").all()
    data = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "marca": p.marca,
            "descripcion": p.descripcion,
            "stock": p.stock,
            "precio": float(p.precio),
            "imagen": p.imagen,
            "categoria": {
                "id": p.categoria_id,
                "nombre": p.categoria.nombre,
                "slug": p.categoria.slug,
            },
        }
        for p in productos
    ]
    return JsonResponse({"productos": data})
