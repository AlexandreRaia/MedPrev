from django.contrib import admin

from apps.apoio.models import EventoSolicitacaoApoio, SolicitacaoApoio


@admin.register(SolicitacaoApoio)
class SolicitacaoApoioAdmin(admin.ModelAdmin):
    list_display = ("servidor_sismed_id", "especialidade", "solicitante", "estado", "criado_em")
    list_filter = ("estado", "especialidade", "unidade")
    search_fields = ("servidor_sismed_id", "solicitante__username")
    readonly_fields = ("criado_em", "respondido_em")
    ordering = ("-criado_em",)


@admin.register(EventoSolicitacaoApoio)
class EventoSolicitacaoApoioAdmin(admin.ModelAdmin):
    list_display = ("solicitacao", "acao", "ator", "criado_em")
    list_filter = ("acao", "criado_em")
    search_fields = ("solicitacao__servidor_sismed_id", "ator__username")
    readonly_fields = ("solicitacao", "ator", "acao", "estado_anterior", "estado_novo", "criado_em")
    ordering = ("-criado_em",)

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
