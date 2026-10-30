import math

from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from usuarios.decorators import admin_required

from .forms import ProductoForm
from .models import Categoria, Productos


@admin_required
@require_POST
def crear_producto(request):
    form = ProductoForm(request.POST, request.FILES)
    if form.is_valid():
        form.save()
        return JsonResponse({'success': True, 'message': 'Producto creado exitosamente'})
    return JsonResponse({'success': False, 'error': 'Datos inválidos', 'errors': form.errors}, status=400)


def lista_productos(request):
    productos = Productos.objects.select_related("categoria").all()
    categoria = request.GET.get("categoria", "").strip()
    busqueda = request.GET.get("q", "").strip()
    orden = request.GET.get("orden", "").strip()

    if categoria:
        productos = productos.filter(categoria__slug=categoria)
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) | Q(marca__icontains=busqueda)
        )

    for parametro, campo, operador in (
        ("precio_min", "precio__gte", "mínimo"),
        ("precio_max", "precio__lte", "máximo"),
    ):
        valor = request.GET.get(parametro)
        if valor in (None, ""):
            continue
        try:
            precio = float(valor)
        except ValueError:
            return JsonResponse(
                {"error": f"El precio {operador} debe ser numérico."},
                status=400,
            )
        if not math.isfinite(precio):
            return JsonResponse(
                {"error": f"El precio {operador} debe ser un número finito."},
                status=400,
            )
        productos = productos.filter(**{campo: precio})

    if (
        request.GET.get("precio_min") not in (None, "")
        and request.GET.get("precio_max") not in (None, "")
        and float(request.GET["precio_min"]) > float(request.GET["precio_max"])
    ):
        return JsonResponse(
            {"error": "El precio mínimo no puede superar el precio máximo."},
            status=400,
        )

    ordenamientos = {
        "precio_asc": "precio",
        "precio_desc": "-precio",
        "nombre_asc": "nombre",
    }
    if orden:
        if orden not in ordenamientos:
            return JsonResponse({"error": "Ordenamiento no válido."}, status=400)
        productos = productos.order_by(ordenamientos[orden], "id")
    else:
        productos = productos.order_by("id")

    total = productos.count()
    datos_productos = [
        {
            "id": producto.id,
            "nombre": producto.nombre,
            "marca": producto.marca,
            "descripcion": producto.descripcion,
            "stock": producto.stock,
            "precio": producto.precio,
            "imagen": producto.imagen,
            "categoria": {
                "id": producto.categoria_id,
                "nombre": producto.categoria.nombre,
                "slug": producto.categoria.slug,
            },
        }
        for producto in productos
    ]
    categorias = list(Categoria.objects.values("id", "nombre", "slug"))
    return JsonResponse(
        {"productos": datos_productos, "categorias": categorias, "total": total}
    )
