import json
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.forms import URLField, ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from productos.models import Categoria, Productos
from usuarios.decorators import admin_required
from .models import (
    DetallePedido,
    MovimientoFinanciero,
    MovimientoInventario,
    Pedidos,
)


def _json_body(request):
    try:
        return json.loads(request.body or "{}"), None
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None, JsonResponse({"error": "El cuerpo JSON no es válido."}, status=400)


def _serialize_product(producto):
    return {
        "id": producto.id,
        "nombre": producto.nombre,
        "marca": producto.marca,
        "descripcion": producto.descripcion,
        "stock": producto.stock,
        "precio": float(producto.precio),
        "imagen": producto.imagen,
        "categoria": {
            "id": producto.categoria_id,
            "nombre": producto.categoria.nombre,
            "slug": producto.categoria.slug,
        },
    }


def _serialize_order(pedido):
    detalles = [
        {
            "producto_id": detalle.id_producto_id,
            "producto": detalle.id_producto.nombre,
            "cantidad": detalle.cantidad,
            "precio_unitario": float(detalle.precio_unitario),
            "subtotal": float(detalle.precio_unitario * detalle.cantidad),
        }
        for detalle in pedido.detalles.select_related("id_producto").all()
    ]
    return {
        "id": pedido.id,
        "cliente": pedido.id_usuario.nombre,
        "email": pedido.id_usuario.email,
        "fecha": pedido.fecha.isoformat(),
        "estado": pedido.estado,
        "pago_confirmado": pedido.pago_confirmado,
        "fecha_pago": pedido.fecha_pago.isoformat() if pedido.fecha_pago else None,
        "total": float(pedido.total),
        "detalles": detalles,
    }


def _serialize_inventory(movimiento):
    return {
        "id": movimiento.id,
        "producto_id": movimiento.producto_id,
        "producto": movimiento.producto.nombre,
        "tipo": movimiento.tipo,
        "cantidad": movimiento.cantidad,
        "stock_anterior": movimiento.stock_anterior,
        "stock_nuevo": movimiento.stock_nuevo,
        "motivo": movimiento.motivo,
        "fecha": movimiento.fecha.isoformat(),
        "responsable": movimiento.responsable.nombre if movimiento.responsable else "Sistema",
    }


def _serialize_finance(movimiento):
    return {
        "id": movimiento.id,
        "tipo": movimiento.tipo,
        "concepto": movimiento.concepto,
        "importe": float(movimiento.importe),
        "fecha": movimiento.fecha.isoformat(),
        "observaciones": movimiento.observaciones,
        "pedido_id": movimiento.pedido_id,
        "responsable": movimiento.responsable.nombre if movimiento.responsable else "Sistema",
    }


@csrf_protect
@admin_required
@require_http_methods(["GET"])
def admin_dashboard(request):
    hoy = timezone.localdate()
    desde = hoy - timedelta(days=29)
    productos = Productos.objects.select_related("categoria")
    ingresos = MovimientoFinanciero.objects.filter(tipo="ingreso")
    egresos = MovimientoFinanciero.objects.filter(tipo="egreso")

    ingresos_por_dia = {
        row["fecha"]: row["total"]
        for row in ingresos.filter(fecha__gte=desde, fecha__lte=hoy)
        .values("fecha").annotate(total=Sum("importe"))
    }
    egresos_por_dia = {
        row["fecha"]: row["total"]
        for row in egresos.filter(fecha__gte=desde, fecha__lte=hoy)
        .values("fecha").annotate(total=Sum("importe"))
    }
    chart = []
    for offset in range(29, -1, -1):
        dia = hoy - timedelta(days=offset)
        chart.append({
            "fecha": dia.isoformat(),
            "ingresos": float(ingresos_por_dia.get(dia, 0)),
            "egresos": float(egresos_por_dia.get(dia, 0)),
        })

    pedidos = Pedidos.objects.select_related("id_usuario").order_by("-fecha", "-id")
    movimientos = MovimientoInventario.objects.select_related(
        "producto", "responsable"
    ).all()
    return JsonResponse({
        "kpis": {
            "productos": productos.count(),
            "unidades_inventario": productos.aggregate(total=Sum("stock"))["total"] or 0,
            "ingresos": float(ingresos.aggregate(total=Sum("importe"))["total"] or 0),
            "egresos": float(egresos.aggregate(total=Sum("importe"))["total"] or 0),
            "balance": float(
                (ingresos.aggregate(total=Sum("importe"))["total"] or 0)
                - (egresos.aggregate(total=Sum("importe"))["total"] or 0)
            ),
            "pedidos_pendientes": Pedidos.objects.filter(estado="Pendiente").count(),
            "pedidos_completados": Pedidos.objects.filter(estado="Completado").count(),
            "pedidos_cancelados": Pedidos.objects.filter(estado="Cancelado").count(),
            "ventas_pagadas": Pedidos.objects.filter(pago_confirmado=True).count(),
            "stock_bajo": productos.filter(stock__lte=5).count(),
        },
        "ventas_diarias": chart,
        "pedidos_recientes": [
            _serialize_order(pedido) for pedido in pedidos[:8]
        ],
        "transacciones_recientes": [
            _serialize_finance(movimiento)
            for movimiento in MovimientoFinanciero.objects.select_related(
                "responsable", "pedido"
            )[:8]
        ],
        "movimientos_recientes": [
            _serialize_inventory(movimiento) for movimiento in movimientos[:8]
        ],
    })


@transaction.atomic
@csrf_protect
@admin_required
@require_http_methods(["GET", "POST"])
def admin_productos(request):
    if request.method == "POST":
        payload, error = _json_body(request)
        if error:
            return error
        try:
            precio = Decimal(str(payload.get("precio", "")))
            stock = int(payload.get("stock", ""))
            categoria = Categoria.objects.get(pk=payload.get("categoria_id"))
        except (InvalidOperation, TypeError, ValueError, Categoria.DoesNotExist):
            return JsonResponse({"error": "Precio, stock o categoría inválidos."}, status=400)
        if not precio.is_finite() or precio <= 0 or stock < 0:
            return JsonResponse({"error": "El precio debe ser positivo y el stock no negativo."}, status=400)
        nombre = str(payload.get("nombre", "")).strip()
        if not nombre or len(nombre) > 100:
            return JsonResponse({"error": "El nombre es obligatorio (máximo 100 caracteres)."}, status=400)
        imagen = str(payload.get("imagen", "")).strip()
        try:
            imagen = URLField(required=False).clean(imagen) or None
        except ValidationError:
            return JsonResponse({"error": "La URL de imagen no es válida."}, status=400)
        producto = Productos.objects.create(
            nombre=nombre,
            marca=str(payload.get("marca", "")).strip()[:100],
            descripcion=str(payload.get("descripcion", "")).strip()[:200],
            categoria=categoria,
            precio=float(precio),
            stock=stock,
            imagen=imagen,
        )
        if stock:
            MovimientoInventario.objects.create(
                producto=producto,
                tipo="entrada",
                cantidad=stock,
                stock_anterior=0,
                stock_nuevo=stock,
                motivo="Existencia inicial al crear producto.",
                responsable=request.admin_user,
                clave_idempotencia=f"producto:{producto.id}:stock-inicial",
            )
        return JsonResponse({"producto": _serialize_product(producto)}, status=201)

    queryset = Productos.objects.select_related("categoria").all()
    q = request.GET.get("q", "").strip()
    categoria = request.GET.get("categoria", "").strip()
    orden = request.GET.get("orden", "nombre_asc")
    if q:
        queryset = queryset.filter(Q(nombre__icontains=q) | Q(marca__icontains=q))
    if categoria:
        queryset = queryset.filter(categoria__slug=categoria)
    ordering = {"nombre_asc": "nombre", "precio_asc": "precio", "precio_desc": "-precio"}
    if orden not in ordering:
        return JsonResponse({"error": "Ordenamiento inválido."}, status=400)
    data = [_serialize_product(producto) for producto in queryset.order_by(ordering[orden], "id")]
    return JsonResponse({"productos": data, "categorias": list(
        Categoria.objects.values("id", "nombre", "slug")
    )})


@transaction.atomic
@csrf_protect
@admin_required
@require_http_methods(["PATCH", "DELETE"])
def admin_producto(request, producto_id):
    try:
        producto = Productos.objects.select_for_update().select_related("categoria").get(pk=producto_id)
    except Productos.DoesNotExist:
        return JsonResponse({"error": "Producto no encontrado."}, status=404)
    if request.method == "DELETE":
        if DetallePedido.objects.filter(id_producto=producto).exists():
            return JsonResponse({
                "error": "No se puede eliminar: el producto tiene pedidos históricos."
            }, status=409)
        if MovimientoInventario.objects.filter(producto=producto).exists():
            return JsonResponse({
                "error": "No se puede eliminar: el producto tiene historial de inventario."
            }, status=409)
        producto.delete()
        return JsonResponse({"success": True})

    payload, error = _json_body(request)
    if error:
        return error
    try:
        precio = Decimal(str(payload.get("precio", producto.precio)))
        stock = int(payload.get("stock", producto.stock))
        categoria = Categoria.objects.get(pk=payload.get("categoria_id", producto.categoria_id))
    except (InvalidOperation, TypeError, ValueError, Categoria.DoesNotExist):
        return JsonResponse({"error": "Precio, stock o categoría inválidos."}, status=400)
    nombre = str(payload.get("nombre", producto.nombre)).strip()
    if not nombre or len(nombre) > 100 or not precio.is_finite() or precio <= 0 or stock < 0:
        return JsonResponse({"error": "Revisa nombre, precio y stock del producto."}, status=400)
    if stock != producto.stock:
        return JsonResponse({
            "error": "El stock se modifica desde la sección Inventario para conservar el historial."
        }, status=400)
    imagen = str(payload.get("imagen", producto.imagen or "")).strip()
    try:
        imagen = URLField(required=False).clean(imagen) or None
    except ValidationError:
        return JsonResponse({"error": "La URL de imagen no es válida."}, status=400)
    producto.nombre = nombre
    producto.marca = str(payload.get("marca", producto.marca)).strip()[:100]
    producto.descripcion = str(payload.get("descripcion", producto.descripcion or "")).strip()[:200]
    producto.imagen = imagen
    producto.categoria = categoria
    producto.precio = float(precio)
    producto.stock = stock
    producto.save()
    return JsonResponse({"producto": _serialize_product(producto)})


@csrf_protect
@admin_required
@require_http_methods(["GET", "POST"])
def admin_inventario(request):
    if request.method == "POST":
        payload, error = _json_body(request)
        if error:
            return error
        key = request.headers.get("Idempotency-Key", "").strip()
        if not key:
            return JsonResponse({"error": "Falta la clave de idempotencia."}, status=400)
        existente = MovimientoInventario.objects.filter(clave_idempotencia=key).first()
        if existente:
            return JsonResponse({
                "movimiento": _serialize_inventory(existente),
                "repetido": True,
            })
        try:
            cantidad = int(payload.get("cantidad"))
            producto_id = int(payload.get("producto_id"))
            tipo = payload.get("tipo")
            motivo = str(payload.get("motivo", "")).strip()
            if cantidad < 0 or tipo not in {"entrada", "salida", "ajuste"} or not motivo:
                raise ValueError
            if tipo in {"entrada", "salida"} and cantidad == 0:
                raise ValueError
        except (TypeError, ValueError):
            return JsonResponse({"error": "Tipo, cantidad y motivo obligatorio no son válidos."}, status=400)

        try:
            with transaction.atomic():
                producto = Productos.objects.select_for_update().get(pk=producto_id)
                anterior = producto.stock
                nuevo = (
                    anterior + cantidad if tipo == "entrada"
                    else anterior - cantidad if tipo == "salida"
                    else cantidad
                )
                if nuevo < 0:
                    return JsonResponse({"error": "La salida supera el stock disponible."}, status=400)
                producto.stock = nuevo
                producto.save(update_fields=["stock"])
                movimiento = MovimientoInventario.objects.create(
                    producto=producto,
                    tipo=tipo,
                    cantidad=abs(nuevo - anterior),
                    stock_anterior=anterior,
                    stock_nuevo=nuevo,
                    motivo=motivo[:200],
                    responsable=request.admin_user,
                    clave_idempotencia=key,
                )
        except Productos.DoesNotExist:
            return JsonResponse({"error": "Producto no encontrado."}, status=404)
        except IntegrityError:
            movimiento = MovimientoInventario.objects.get(clave_idempotencia=key)
            return JsonResponse({"movimiento": _serialize_inventory(movimiento), "repetido": True})
        return JsonResponse({"movimiento": _serialize_inventory(movimiento)}, status=201)

    queryset = MovimientoInventario.objects.select_related("producto", "responsable")
    return JsonResponse({
        "productos": [
            {"id": item.id, "nombre": item.nombre, "stock": item.stock}
            for item in Productos.objects.order_by("nombre")
        ],
        "movimientos": [_serialize_inventory(item) for item in queryset[:200]],
    })


@csrf_protect
@admin_required
@require_http_methods(["GET"])
def admin_pedidos(request):
    queryset = Pedidos.objects.select_related("id_usuario").order_by("-fecha", "-id")
    estado = request.GET.get("estado", "").strip()
    desde = request.GET.get("fecha_desde", "").strip()
    hasta = request.GET.get("fecha_hasta", "").strip()
    if estado:
        if estado not in dict(Pedidos.ESTADOS):
            return JsonResponse({"error": "Estado inválido."}, status=400)
        queryset = queryset.filter(estado=estado)
    try:
        if desde:
            queryset = queryset.filter(fecha__gte=date.fromisoformat(desde))
        if hasta:
            queryset = queryset.filter(fecha__lte=date.fromisoformat(hasta))
    except ValueError:
        return JsonResponse({"error": "Formato de fecha inválido."}, status=400)
    return JsonResponse({"pedidos": [_serialize_order(item) for item in queryset[:200]]})


@csrf_protect
@admin_required
@require_http_methods(["PATCH"])
def admin_actualizar_pedido(request, pedido_id):
    payload, error = _json_body(request)
    if error:
        return error
    estado = payload.get("estado")
    if estado not in dict(Pedidos.ESTADOS):
        return JsonResponse({"error": "Estado inválido."}, status=400)
    try:
        with transaction.atomic():
            pedido = Pedidos.objects.select_for_update().get(pk=pedido_id)
            if pedido.pago_confirmado and estado == "Cancelado":
                return JsonResponse({
                    "error": "Una venta pagada no se puede cancelar sin un proceso de reembolso."
                }, status=409)
            if pedido.estado == "Cancelado" and estado != "Cancelado":
                return JsonResponse({"error": "Un pedido cancelado no se puede reactivar."}, status=409)
            if estado == "Cancelado" and pedido.estado != "Cancelado":
                for detalle in pedido.detalles.select_related("id_producto").all():
                    producto = Productos.objects.select_for_update().get(pk=detalle.id_producto_id)
                    anterior = producto.stock
                    producto.stock += detalle.cantidad
                    producto.save(update_fields=["stock"])
                    MovimientoInventario.objects.get_or_create(
                        clave_idempotencia=f"pedido:{pedido.id}:cancelacion:{producto.id}",
                        defaults={
                            "producto": producto,
                            "tipo": "entrada",
                            "cantidad": detalle.cantidad,
                            "stock_anterior": anterior,
                            "stock_nuevo": producto.stock,
                            "motivo": f"Reposición de pedido cancelado #{pedido.id}",
                            "responsable": request.admin_user,
                        },
                    )
            pedido.estado = estado
            pedido.save(update_fields=["estado"])
    except Pedidos.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado."}, status=404)
    return JsonResponse({"pedido": _serialize_order(pedido)})


@csrf_protect
@admin_required
@require_http_methods(["POST"])
def admin_confirmar_pago(request, pedido_id):
    try:
        with transaction.atomic():
            pedido = Pedidos.objects.select_for_update().get(pk=pedido_id)
            if pedido.estado == "Cancelado":
                return JsonResponse({"error": "No se puede registrar el pago de un pedido cancelado."}, status=409)
            if not pedido.pago_confirmado:
                importe = sum(
                    (detalle.precio_unitario * detalle.cantidad)
                    for detalle in pedido.detalles.all()
                )
                if importe <= 0:
                    return JsonResponse({"error": "El pedido no tiene un total válido."}, status=400)
                pedido.total = importe
                pedido.pago_confirmado = True
                pedido.fecha_pago = timezone.now()
                pedido.estado = "Completado"
                pedido.save(update_fields=["total", "pago_confirmado", "fecha_pago", "estado"])
                MovimientoFinanciero.objects.get_or_create(
                    pedido=pedido,
                    defaults={
                        "tipo": "ingreso",
                        "concepto": f"Venta pedido #{pedido.id}",
                        "importe": importe,
                        "fecha": timezone.localdate(),
                        "responsable": request.admin_user,
                    },
                )
    except Pedidos.DoesNotExist:
        return JsonResponse({"error": "Pedido no encontrado."}, status=404)
    return JsonResponse({"pedido": _serialize_order(pedido)})


@csrf_protect
@admin_required
@require_http_methods(["GET", "POST"])
def admin_finanzas(request):
    if request.method == "POST":
        payload, error = _json_body(request)
        if error:
            return error
        key = request.headers.get("Idempotency-Key", "").strip()
        if not key:
            return JsonResponse({"error": "Falta la clave de idempotencia."}, status=400)
        existente = MovimientoFinanciero.objects.filter(clave_idempotencia=key).first()
        if existente:
            return JsonResponse({"movimiento": _serialize_finance(existente), "repetido": True})
        tipo = payload.get("tipo")
        concepto = str(payload.get("concepto", "")).strip()
        try:
            importe = Decimal(str(payload.get("importe", "")))
            fecha = date.fromisoformat(payload.get("fecha") or timezone.localdate().isoformat())
        except (InvalidOperation, TypeError, ValueError):
            return JsonResponse({"error": "Importe o fecha inválidos."}, status=400)
        if tipo not in {"ingreso", "egreso"} or not concepto or len(concepto) > 160:
            return JsonResponse({"error": "Tipo y concepto válido son obligatorios."}, status=400)
        if not importe.is_finite() or importe <= 0:
            return JsonResponse({"error": "El importe debe ser mayor que cero."}, status=400)
        try:
            movimiento = MovimientoFinanciero.objects.create(
                tipo=tipo,
                concepto=concepto,
                importe=importe,
                fecha=fecha,
                observaciones=str(payload.get("observaciones", "")).strip()[:500],
                responsable=request.admin_user,
                clave_idempotencia=key,
            )
        except IntegrityError:
            movimiento = MovimientoFinanciero.objects.get(clave_idempotencia=key)
            return JsonResponse({"movimiento": _serialize_finance(movimiento), "repetido": True})
        return JsonResponse({"movimiento": _serialize_finance(movimiento)}, status=201)

    queryset = MovimientoFinanciero.objects.select_related("pedido", "responsable")
    tipo = request.GET.get("tipo", "").strip()
    desde = request.GET.get("fecha_desde", "").strip()
    hasta = request.GET.get("fecha_hasta", "").strip()
    concepto = request.GET.get("q", "").strip()
    if tipo:
        if tipo not in {"ingreso", "egreso"}:
            return JsonResponse({"error": "Tipo inválido."}, status=400)
        queryset = queryset.filter(tipo=tipo)
    try:
        if desde:
            queryset = queryset.filter(fecha__gte=date.fromisoformat(desde))
        if hasta:
            queryset = queryset.filter(fecha__lte=date.fromisoformat(hasta))
    except ValueError:
        return JsonResponse({"error": "Formato de fecha inválido."}, status=400)
    if concepto:
        queryset = queryset.filter(concepto__icontains=concepto)
    return JsonResponse({"movimientos": [_serialize_finance(item) for item in queryset[:200]]})


@csrf_protect
@admin_required
@require_http_methods(["GET"])
def admin_movimientos(request):
    queryset = MovimientoInventario.objects.select_related("producto", "responsable")
    return JsonResponse({
        "movimientos": [_serialize_inventory(item) for item in queryset[:300]]
    })
