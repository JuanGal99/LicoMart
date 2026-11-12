from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
class Usuarios(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    email = models.EmailField(max_length=254, unique=True)
    contraseña = models.CharField(max_length=256)
    rol = models.CharField(max_length=50, default='usuario')

    def set_password(self, raw_password):
        self.contraseña = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.contraseña)

    def __str__(self):
        return self.nombre
    
