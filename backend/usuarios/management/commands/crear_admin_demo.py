import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from usuarios.models import Usuarios


class Command(BaseCommand):
    help = "Crea de forma idempotente la cuenta de administrador local de demostración."

    username = "admin_demo"
    email = "admin-demo@licomart.local"
    password = "LicoMartDemo2026!"

    def handle(self, *args, **options):
        if not settings.DEBUG or os.environ.get("ALLOW_DEMO_ADMIN") != "true":
            raise CommandError(
                "La cuenta de demostración solo se puede crear con DEBUG=true "
                "y ALLOW_DEMO_ADMIN=true."
            )

        usuario, creado = Usuarios.objects.get_or_create(
            nombre=self.username,
            defaults={
                "email": self.email,
                "rol": "admin",
                "contraseña": "",
            },
        )
        if not creado and (usuario.email != self.email or usuario.rol != "admin"):
            raise CommandError(
                "Ya existe admin_demo con otros datos. No se modificó esa cuenta."
            )
        if creado:
            usuario.set_password(self.password)
            usuario.save(update_fields=["contraseña"])
            self.stdout.write(self.style.SUCCESS("Administrador demo creado."))
        else:
            self.stdout.write("El administrador demo ya existe; no se modificó.")

        self.stdout.write(f"Usuario: {self.username}")
        self.stdout.write(f"Contraseña: {self.password}")
