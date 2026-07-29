from django.contrib import admin

from apps.pareceres.models import EventoParecer, Parecer


@admin.register(Parecer)
class ParecerAdmin(admin.ModelAdmin):
    list_display = ("servidor_sismed_id", "autor", "conclusao", "estado", "criado_em")
    list_filter = ("estado", "conclusao", "unidade")
    search_fields = ("servidor_sismed_id", "autor__username")
    readonly_fields = ("criado_em", "atualizado_em", "concluido_em")
    ordering = ("-criado_em",)


@admin.register(EventoParecer)
class EventoParecerAdmin(admin.ModelAdmin):
    list_display = ("parecer", "acao", "ator", "criado_em")
    list_filter = ("acao", "criado_em")
    search_fields = ("parecer__servidor_sismed_id", "ator__username")
    readonly_fields = ("parecer", "ator", "acao", "estado_anterior", "estado_novo", "criado_em")
    ordering = ("-criado_em",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
