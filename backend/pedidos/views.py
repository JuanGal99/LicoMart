from django.http import JsonResponse
import datetime
from .forms import PedidoForm, DetallePedidoFormSet
from django.db.models import Sum, F
from .models import Pedidos, DetallePedido
from django.db.models.functions import Concat
from django.db.models import Value as V
from django.views.decorators.csrf import csrf_exempt
from usuarios.decorators import admin_required
import json

def pedidos(request):
    return JsonResponse({'success': True, 'message': 'Vista de pedidos'})

@admin_required
def crear_pedido(request):
    if request.method == "POST":
        pedido_form = PedidoForm(request.POST)
        formset = DetallePedidoFormSet(request.POST)

        if pedido_form.is_valid() and formset.is_valid():
            pedido = pedido_form.save(commit=False)
            if isinstance(pedido.fecha, str):
                try:
                    pedido.fecha = datetime.strptime(pedido.fecha, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'})

            pedido.save()
            detalles = formset.save(commit=False)
            for detalle in detalles:
                detalle.id_pedido = pedido
                detalle.save()
            return JsonResponse({'success': True, 'message': 'Pedido creado exitosamente'})

        return JsonResponse({'success': False, 'error': 'Datos inválidos', 'errors': pedido_form.errors})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


@csrf_exempt
@admin_required
def crear_pedido_json(request):
    """Crea un pedido y sus detalles desde JSON.
    Body esperado:
    {
      "usuario_id": 6,
      "fecha": "2025-10-31",  # opcional, por defecto hoy
      "estado": "Pendiente",  # opcional
      "detalles": [ {"producto_id": 1, "cantidad": 2}, ... ]
    }
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
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

    created_count = 0
    for d in detalles:
        pid = d.get('producto_id')
        cantidad = d.get('cantidad')
        if not pid or not cantidad or cantidad <= 0:
            continue
        try:
            prod = Productos.objects.get(id=pid)
        except Productos.DoesNotExist:
            continue
        DetallePedido.objects.create(id_pedido=pedido, id_producto=prod, cantidad=cantidad)
        created_count += 1

    return JsonResponse({'success': True, 'message': 'Pedido creado', 'pedido_id': pedido.id, 'detalles_creados': created_count})


def actualizar_estado_pedido(request, pedido_id: int):
    from .admin_views import admin_actualizar_pedido

    return admin_actualizar_pedido(request, pedido_id)


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
            'ingresosMes': ingresos_mes,
        }
    })


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


@admin_required
def pedidos_recientes(request):
    # Lista de pedidos recientes con cliente, estado y fecha.
    try:
        limit = int(request.GET.get('limit', 10))
        pedidos = (Pedidos.objects
                   .select_related('id_usuario')
                   .order_by('-fecha', '-id')[:limit])
        
        data = [{
            'id': p.id,
            'cliente': p.id_usuario.nombre,
            'estado': p.estado,
            'fecha': p.fecha.strftime('%Y-%m-%d')
        } for p in pedidos]
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


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
                   .select_related('id_producto', 'id_pedido')
                   .order_by('id_pedido__id'))
        
        # Construir la respuesta
        data = []
        for detalle in detalles:
            pedido = detalle.id_pedido
            producto = detalle.id_producto
            
            item = {
                'id_pedido': pedido.id,
                'tienda': 'Licomart',  # Por defecto es Licomart, se puede modificar si se integra con otra tienda
                'nombre_cliente': pedido.id_usuario.nombre,
                'nombre_producto': producto.nombre,
                'cantidad': detalle.cantidad,
                'precio': float(producto.precio),
                'fecha': pedido.fecha.strftime('%Y-%m-%d')
            }
            
            # Aplicar filtros adicionales
            if tienda and tienda.lower() != item['tienda'].lower():
                continue
            if cliente and cliente not in item['nombre_cliente'].lower():
                continue
            if producto_filtro and producto_filtro not in item['nombre_producto'].lower():
                continue
                
            data.append(item)
            
        # Si no hay filtros aplicados, devolver todos los pedidos completados
        if not any([fecha_desde, fecha_hasta, tienda, cliente, producto_filtro]) and not data:
            # Si no hay datos, verificar si hay pedidos completados
            if not pedidos.exists():
                return JsonResponse({'success': True, 'data': []})
        
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
