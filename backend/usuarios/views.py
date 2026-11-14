import json

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from django.db.models import Q

from .models import Usuarios

@ensure_csrf_cookie
@require_POST
def login_view(request):
    try:
        data = json.loads(request.body)
        identifier = data.get('identifier')
        password = data.get('password')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    if not identifier or not password:
        return JsonResponse({'success': False, 'error': 'Faltan campos'}, status=400)

    try:
        usuario = Usuarios.objects.get(
            Q(nombre=identifier) | Q(email=identifier)
        )

        if usuario.check_password(password):
            request.session.cycle_key()
            request.session['usuario_id'] = usuario.id
            return JsonResponse({
                'success': True,
                'message': 'Inicio de sesión exitoso',
                'usuario_id': usuario.id,
                'nombre': usuario.nombre,
                'email': usuario.email,
                'rol': usuario.rol,
            })
        else:
            return JsonResponse({'success': False, 'error': 'Contraseña incorrecta'}, status=401)
    except Usuarios.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Usuario o correo no encontrado'}, status=401)



@ensure_csrf_cookie
def csrf_token_view(request):
    return JsonResponse({"success": True})


def current_user_view(request):
    usuario_id = request.session.get("usuario_id")
    if not usuario_id:
        return JsonResponse({"authenticated": False}, status=401)
    try:
        usuario = Usuarios.objects.get(pk=usuario_id)
    except Usuarios.DoesNotExist:
        request.session.flush()
        return JsonResponse({"authenticated": False}, status=401)
    return JsonResponse({
        "authenticated": True,
        "usuario_id": usuario.id,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "rol": usuario.rol,
    })


@require_POST
def register_view(request):
    try:
        data = json.loads(request.body)
        username = str(data.get('username', '')).strip()
        email = str(data.get('email', '')).strip().lower()
        password = data.get('password')
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

    if not username or not email or not password:
        return JsonResponse({'success': False, 'error': 'Faltan campos obligatorios'}, status=400)

    if len(username) > 60:
        return JsonResponse({'success': False, 'error': 'El nombre de usuario es demasiado largo (máximo 60 caracteres).'}, status=400)

    try:
        validate_email(email)
    except ValidationError:
        return JsonResponse({'success': False, 'error': 'El formato del correo no es válido.'}, status=400)

    try:
        validate_password(password)
    except ValidationError as e:
        return JsonResponse({'success': False, 'error': e.messages[0]}, status=400)

    if Usuarios.objects.filter(nombre=username).exists():
        return JsonResponse({'success': False, 'error': 'El nombre de usuario ya está en uso.'}, status=409)
    if Usuarios.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'error': 'El correo ya está en uso.'}, status=409)

    nuevo_usuario = Usuarios(nombre=username, email=email, rol='usuario')
    nuevo_usuario.set_password(password)
    nuevo_usuario.save()

    return JsonResponse({'success': True, 'message': 'Usuario registrado exitosamente'})


@require_POST
def singout(request):
    request.session.flush()
    return JsonResponse({'success': True, 'message': 'Sesión cerrada exitosamente'})
