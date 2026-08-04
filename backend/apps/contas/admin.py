from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.contas.models import EventoAcesso, EventoAutenticacao, Unidade, Usuario


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """Administração de usuários usando os controles nativos do Django."""

    list_display = ("username", "email", "unidade", "is_active", "is_staff")
    list_filter = ("unidade", "is_active", "groups")
    fieldsets = UserAdmin.fieldsets + (("MedPrev", {"fields": ("unidade", "deve_trocar_senha")}),)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("MedPrev", {"fields": ("unidade", "deve_trocar_senha")}),
    )


@admin.register(Unidade)
class UnidadeAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "tipo", "ativa")
    list_filter = ("tipo", "ativa")
    search_fields = ("nome", "codigo")


@admin.register(EventoAutenticacao)
class EventoAutenticacaoAdmin(admin.ModelAdmin):
    list_display = ("tipo", "usuario", "identificador", "criado_em")
    list_filter = ("tipo", "criado_em")
    search_fields = ("usuario__username", "identificador")
    readonly_fields = ("usuario", "identificador", "tipo", "criado_em")
    ordering = ("-criado_em",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EventoAcesso)
class EventoAcessoAdmin(admin.ModelAdmin):
    list_display = ("acao", "usuario_alvo", "ator", "criado_em")
    list_filter = ("acao", "criado_em")
    search_fields = ("usuario_alvo__username", "ator__username")
    readonly_fields = ("ator", "usuario_alvo", "acao", "detalhes", "criado_em")
    ordering = ("-criado_em",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
