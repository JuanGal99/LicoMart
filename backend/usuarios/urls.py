from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.singout, name='logout'),
    path('csrf/', views.csrf_token_view, name='csrf_token'),
    path('me/', views.current_user_view, name='current_user'),
]
