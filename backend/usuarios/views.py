from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from .models import Usuarios
import json

@ensure_csrf_cookie
def login_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            identifier = data.get('identifier')
            password = data.get('password')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

        if not identifier or not password:
            return JsonResponse({'success': False, 'error': 'Faltan campos'}, status=400)

        try:
            try:
                usuario = Usuarios.objects.get(nombre=identifier)
            except Usuarios.DoesNotExist:
                usuario = Usuarios.objects.get(email=identifier)

            if usuario.check_password(password):
                request.session.cycle_key()
                request.session['usuario_id'] = usuario.id  # Si manejas sesión
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

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


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


def register_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            username = data.get('username')
            email = data.get('email')
            password = data.get('password')
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'JSON inválido'}, status=400)

        if not username or not email or not password:
            return JsonResponse({'success': False, 'error': 'Faltan campos obligatorios'}, status=400)

        if Usuarios.objects.filter(nombre=username).exists():
            return JsonResponse({'success': False, 'error': 'El nombre de usuario ya está en uso.'}, status=409)
        if Usuarios.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'El correo ya está en uso.'}, status=409)

        nuevo_usuario = Usuarios(nombre=username, email=email, rol='usuario')
        nuevo_usuario.set_password(password)
        nuevo_usuario.save()

        return JsonResponse({'success': True, 'message': 'Usuario registrado exitosamente'})

    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)


def singout(request):
    if request.method == 'POST':
        request.session.flush()
        return JsonResponse({'success': True, 'message': 'Sesión cerrada exitosamente'})
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'}, status=405)
