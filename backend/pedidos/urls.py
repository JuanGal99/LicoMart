from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    path('', views.pedidos, name='pedido'),
    path('crear/', views.crear_pedido, name='crear_pedido'),
    path('crear-json/', views.crear_pedido_json, name='crear_pedido_json'),
    path('<int:pedido_id>/estado/', views.actualizar_estado_pedido, name='actualizar_estado_pedido'),
    path('kpis/', views.kpis, name='kpis'),
    path('top-vendidos/', views.top_vendidos, name='top_vendidos'),
    path('recientes/', views.pedidos_recientes, name='pedidos_recientes'),
    path('completados/', views.pedidos_completados, name='pedidos_completados'),
    path('admin/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('admin/productos/', admin_views.admin_productos, name='admin_productos'),
    path('admin/productos/<int:producto_id>/', admin_views.admin_producto, name='admin_producto'),
    path('admin/inventario/', admin_views.admin_inventario, name='admin_inventario'),
    path('admin/pedidos/', admin_views.admin_pedidos, name='admin_pedidos'),
    path('admin/pedidos/<int:pedido_id>/', admin_views.admin_actualizar_pedido, name='admin_actualizar_pedido'),
    path('admin/pedidos/<int:pedido_id>/pago/', admin_views.admin_confirmar_pago, name='admin_confirmar_pago'),
    path('admin/finanzas/', admin_views.admin_finanzas, name='admin_finanzas'),
    path('admin/movimientos/', admin_views.admin_movimientos, name='admin_movimientos'),
]
