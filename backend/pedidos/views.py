import datetime
import json

from django.db import transaction
from django.db.models import Sum
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .forms import PedidoForm, DetallePedidoFormSet
from .models import DetallePedido, MovimientoInventario, Pedidos
from usuarios.decorators import admin_required

@require_POST
@transaction.atomic
@admin_required
def crear_pedido(request):
    pedido_form = PedidoForm(request.POST)
    formset = DetallePedidoFormSet(request.POST)

    if not (pedido_form.is_valid() and formset.is_valid()):
        return JsonResponse({'success': False, 'error': 'Datos inválidos', 'errors': pedido_form.errors}, status=400)

    pedido = pedido_form.save(commit=False)
    if isinstance(pedido.fecha, str):
        try:
            pedido.fecha = datetime.datetime.strptime(pedido.fecha, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)

    pedido.save()
    from productos.models import Productos
    detalles = formset.save(commit=False)
    for detalle in detalles:
        producto = Productos.objects.select_for_update().get(pk=detalle.id_producto_id)
        if producto.stock < detalle.cantidad:
            transaction.set_rollback(True)
            return JsonResponse({
                'success': False,
                'error': f'Stock insuficiente para {producto.nombre} ({producto.stock} disponibles)',
            }, status=400)
        detalle.id_pedido = pedido
        detalle.save()
        anterior = producto.stock
        producto.stock -= detalle.cantidad
        producto.save(update_fields=["stock"])
        MovimientoInventario.objects.create(
            producto=producto,
            tipo="salida",
            cantidad=detalle.cantidad,
            stock_anterior=anterior,
            stock_nuevo=producto.stock,
            motivo=f"Pedido admin form #{pedido.id}",
            clave_idempotencia=f"pedido-form:{pedido.id}:reserva:{producto.id}",
        )
    return JsonResponse({'success': True, 'message': 'Pedido creado exitosamente'})


@require_POST
@transaction.atomic
@admin_required
def crear_pedido_json(request):
    try:
        payload = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    usuario_id = payload.get('usuario_id')
    fecha_str = payload.get('fecha')
    estado = payload.get('estado', 'Pendiente')
    detalles = payload.get('detalles', [])

    if not usuario_id or not isinstance(detalles, list) or len(detalles) == 0:
        return JsonResponse({'success': False, 'error': 'usuario_id y detalles son obligatorios'}, status=400)

    # Validaciones
    from usuarios.models import Usuarios
    from productos.models import Productos
    try:
        usuario = Usuarios.objects.get(id=usuario_id)
    except Usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario no encontrado'}, status=404)

    # Parse de fecha
    if fecha_str:
        try:
            fecha = datetime.datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)
    else:
        fecha = datetime.date.today()

    pedido = Pedidos.objects.create(id_usuario=usuario, fecha=fecha, estado=estado)

    skipped = []
    created_count = 0
    for d in detalles:
        pid = d.get('producto_id')
        cantidad = d.get('cantidad')
        if not pid or not cantidad or cantidad <= 0:
            skipped.append(f"producto_id={pid}: cantidad inválida")
            continue
        try:
            prod = Productos.objects.select_for_update().get(id=pid)
        except Productos.DoesNotExist:
            skipped.append(f"producto_id={pid}: no existe")
            continue
        if prod.stock < cantidad:
            skipped.append(f"producto_id={pid}: stock insuficiente ({prod.stock} disponibles, {cantidad} solicitados)")
            continue
        anterior = prod.stock
        prod.stock -= cantidad
        prod.save(update_fields=["stock"])
        DetallePedido.objects.create(id_pedido=pedido, id_producto=prod, cantidad=cantidad)
        MovimientoInventario.objects.create(
            producto=prod,
            tipo="salida",
            cantidad=cantidad,
            stock_anterior=anterior,
            stock_nuevo=prod.stock,
            motivo=f"Pedido admin #{pedido.id}",
            clave_idempotencia=f"pedido-admin:{pedido.id}:reserva:{prod.id}",
        )
        created_count += 1

    if created_count == 0:
        transaction.set_rollback(True)
        return JsonResponse({
            'success': False,
            'error': 'Ningún detalle pudo procesarse',
            'detalles_omitidos': skipped,
        }, status=400)

    return JsonResponse({
        'success': True,
        'message': 'Pedido creado',
        'pedido_id': pedido.id,
        'detalles_creados': created_count,
        'detalles_omitidos': skipped,
    })


def actualizar_estado_pedido(request, pedido_id: int):
    from .admin_views import admin_actualizar_pedido

    return admin_actualizar_pedido(request, pedido_id)


@require_GET
@admin_required
def kpis(request):
    """Devuelve KPIs básicos: pedidos activos, pendientes e ingresos del mes."""
    hoy = datetime.date.today()
    primer_dia_mes = hoy.replace(day=1)

    activos = Pedidos.objects.filter(estado='En Proceso').count()
    pendientes = Pedidos.objects.filter(estado='Pendiente').count()

    ingresos_mes = (
        DetallePedido.objects
            .filter(
                id_pedido__pago_confirmado=True,
                id_pedido__estado='Completado',
                id_pedido__fecha__gte=primer_dia_mes,
                id_pedido__fecha__lte=hoy,
            )
            .aggregate(total=Sum('subtotal'))
            .get('total')
    ) or 0

    return JsonResponse({
        'success': True,
        'data': {
            'activos': activos,
            'pendientes': pendientes,
            'ingresosMes': float(ingresos_mes),
        }
    })


@require_GET
@admin_required
def top_vendidos(request):
    """Top productos por unidades vendidas (sumatoria de cantidad en detalles)."""
    try:
        limit = int(request.GET.get('limit', '5'))
    except ValueError:
        limit = 5

    qs = (
        DetallePedido.objects
        .values('id_producto__nombre')
        .annotate(ventas=Sum('cantidad'))
        .order_by('-ventas')[:limit]
    )

    data = [{
        'producto': r['id_producto__nombre'],
        'ventas': r['ventas']
    } for r in qs]

    return JsonResponse({'success': True, 'data': data})


@require_GET
@admin_required
def pedidos_recientes(request):
    """Lista de pedidos recientes con cliente, estado y fecha."""
    try:
        limit = int(request.GET.get('limit', '10'))
    except ValueError:
        limit = 10

    qs = (
        Pedidos.objects
        .select_related('id_usuario')
        .order_by('-id')[:limit]
    )

    data = [{
        'id': p.id,
        'cliente': p.id_usuario.nombre,
        'estado': p.estado,
        'fecha': p.fecha.strftime('%d/%m/%Y') if isinstance(p.fecha, datetime.date) else str(p.fecha)
    } for p in qs]

    return JsonResponse({'success': True, 'data': data})




@require_GET
@admin_required
def pedidos_completados(request):
    # Lista de pedidos completados con todos los detalles necesarios para la tabla
    try:
        # Obtener parámetros de filtrado
        fecha_desde = request.GET.get('fecha_desde')
        fecha_hasta = request.GET.get('fecha_hasta')
        tienda = request.GET.get('tienda')
        cliente = request.GET.get('cliente', '').lower()
        producto_filtro = request.GET.get('producto', '').lower()
        
        # Obtener solo los pedidos con estado 'Completado'
        pedidos = (Pedidos.objects
                  .filter(estado='Completado')
                  .select_related('id_usuario')
                  .order_by('-fecha', '-id'))
        
        # Aplicar filtros de fecha si están presentes
        if fecha_desde:
            try:
                fecha_desde_dt = datetime.datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                pedidos = pedidos.filter(fecha__gte=fecha_desde_dt)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha_desde inválido. Use YYYY-MM-DD.'}, status=400)
                
        if fecha_hasta:
            try:
                fecha_hasta_dt = datetime.datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                pedidos = pedidos.filter(fecha__lte=fecha_hasta_dt)
            except ValueError:
                return JsonResponse({'success': False, 'error': 'Formato de fecha_hasta inválido. Use YYYY-MM-DD.'}, status=400)
        
        # Obtener los detalles de cada pedido
        detalles = (DetallePedido.objects
                   .filter(id_pedido__in=pedidos)
                   .select_related('id_producto', 'id_pedido', 'id_pedido__id_usuario')
                   .order_by('id_pedido__id'))
        
        if cliente:
            detalles = detalles.filter(id_pedido__id_usuario__nombre__icontains=cliente)
        if producto_filtro:
            detalles = detalles.filter(id_producto__nombre__icontains=producto_filtro)

        data = [
            {
                'id_pedido': detalle.id_pedido_id,
                'tienda': 'Licomart',
                'nombre_cliente': detalle.id_pedido.id_usuario.nombre,
                'nombre_producto': detalle.id_producto.nombre,
                'cantidad': detalle.cantidad,
                'precio': float(detalle.precio_unitario),
                'fecha': detalle.id_pedido.fecha.strftime('%Y-%m-%d'),
            }
            for detalle in detalles
        ]

        return JsonResponse({'success': True, 'data': data})
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Parámetros de filtro inválidos'}, status=400)
