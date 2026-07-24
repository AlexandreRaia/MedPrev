from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.contas.models import Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Administração de usuários usando os controles nativos do Django."""
