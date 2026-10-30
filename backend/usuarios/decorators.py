from functools import wraps

from django.http import JsonResponse

from .models import Usuarios


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        usuario_id = request.session.get("usuario_id")
        if not usuario_id:
            return JsonResponse({"error": "Debes iniciar sesión."}, status=401)

        try:
            usuario = Usuarios.objects.get(pk=usuario_id)
        except Usuarios.DoesNotExist:
            request.session.flush()
            return JsonResponse({"error": "La sesión ya no es válida."}, status=401)

        if usuario.rol != "admin":
            return JsonResponse({"error": "No tienes permisos de administrador."}, status=403)

        request.admin_user = usuario
        return view_func(request, *args, **kwargs)

    return wrapped
