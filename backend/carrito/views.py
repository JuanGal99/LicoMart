import json
from datetime import date

from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from pedidos.models import DetallePedido, MovimientoInventario, Pedidos
from productos.models import Productos
from usuarios.models import Usuarios


def _total(carrito):
    return sum(float(item["precio"]) * int(item["cantidad"]) for item in carrito.values())


@csrf_exempt
def ver_carrito(request):
    carrito = request.session.get("carrito", {})
    return JsonResponse({"carrito": carrito, "total": _total(carrito)})


@csrf_exempt
@transaction.atomic
def confirmar_compra(request):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)

    carrito = request.session.get("carrito", {})
    usuario_id = request.session.get("usuario_id")
    if not carrito:
        return JsonResponse({"success": False, "error": "El carrito está vacío"}, status=400)
    if not usuario_id:
        return JsonResponse({"success": False, "error": "Usuario no autenticado"}, status=401)

    try:
        usuario = Usuarios.objects.get(pk=usuario_id)
    except Usuarios.DoesNotExist:
        request.session.flush()
        return JsonResponse({"success": False, "error": "La sesión ya no es válida"}, status=401)

    cantidades = {}
    try:
        for producto_id, item in carrito.items():
            cantidad = int(item["cantidad"])
            if cantidad <= 0:
                raise ValueError
            cantidades[int(producto_id)] = cantidad
    except (KeyError, TypeError, ValueError):
        return JsonResponse({"success": False, "error": "El carrito contiene cantidades inválidas"}, status=400)

    productos = {
        producto.pk: producto
        for producto in Productos.objects.select_for_update()
        .filter(pk__in=cantidades)
        .order_by("pk")
    }
    if len(productos) != len(cantidades):
        return JsonResponse({"success": False, "error": "Un producto del carrito ya no existe"}, status=400)
    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        if producto.stock < cantidad:
            return JsonResponse({
                "success": False,
                "error": f"No hay suficiente stock para {producto.nombre}",
            }, status=400)

    pedido = Pedidos.objects.create(
        id_usuario=usuario,
        fecha=date.today(),
        estado="Pendiente",
    )
    total = 0
    for producto_id, cantidad in cantidades.items():
        producto = productos[producto_id]
        precio_unitario = producto.precio
        subtotal = precio_unitario * cantidad
        total += subtotal
        DetallePedido.objects.create(
            id_pedido=pedido,
            id_producto=producto,
            cantidad=cantidad,
            precio_unitario=precio_unitario,
        )
        anterior = producto.stock
        producto.stock -= cantidad
        producto.save(update_fields=["stock"])
        MovimientoInventario.objects.create(
            producto=producto,
            tipo="salida",
            cantidad=cantidad,
            stock_anterior=anterior,
            stock_nuevo=producto.stock,
            motivo=f"Reserva de pedido #{pedido.id}",
            clave_idempotencia=f"pedido:{pedido.id}:reserva:{producto.id}",
        )

    pedido.total = total
    pedido.save(update_fields=["total"])
    request.session["carrito"] = {}
    return JsonResponse({
        "success": True,
        "message": "Pedido creado; el pago está pendiente de confirmación.",
        "pedido_id": pedido.id,
        "total": float(total),
    })


@csrf_exempt
def agregar_al_carrito(request, producto_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
    try:
        payload = json.loads(request.body or "{}")
        cantidad = int(payload.get("cantidad", 1))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"success": False, "error": "Cantidad inválida"}, status=400)
    if cantidad <= 0:
        return JsonResponse({"success": False, "error": "La cantidad debe ser mayor que cero"}, status=400)

    try:
        producto = Productos.objects.get(pk=producto_id)
    except Productos.DoesNotExist:
        return JsonResponse({"success": False, "error": "Producto no encontrado"}, status=404)

    carrito = request.session.get("carrito", {})
    key = str(producto_id)
    actual = int(carrito.get(key, {}).get("cantidad", 0))
    disponible = producto.stock - actual
    if cantidad > disponible:
        return JsonResponse({"success": False, "error": "La cantidad supera el stock disponible"}, status=400)

    if key in carrito:
        carrito[key]["cantidad"] += cantidad
    else:
        carrito[key] = {
            "nombre": producto.nombre,
            "precio": producto.precio,
            "cantidad": cantidad,
        }
    request.session["carrito"] = carrito
    return JsonResponse({
        "success": True,
        "message": "Producto agregado al carrito",
        "carrito": carrito,
        "total": _total(carrito),
    })


@csrf_exempt
def eliminar_del_carrito(request, producto_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Método no permitido"}, status=405)
    try:
        payload = json.loads(request.body or "{}")
        cantidad = int(payload.get("cantidad", 1))
    except (json.JSONDecodeError, TypeError, ValueError):
        return JsonResponse({"success": False, "error": "Cantidad inválida"}, status=400)
    if cantidad <= 0:
        return JsonResponse({"success": False, "error": "La cantidad debe ser mayor que cero"}, status=400)

    carrito = request.session.get("carrito", {})
    key = str(producto_id)
    if key in carrito:
        restante = int(carrito[key]["cantidad"]) - cantidad
        if restante > 0:
            carrito[key]["cantidad"] = restante
        else:
            del carrito[key]
    request.session["carrito"] = carrito
    return JsonResponse({
        "success": True,
        "message": "Carrito actualizado",
        "carrito": carrito,
        "total": _total(carrito),
    })
