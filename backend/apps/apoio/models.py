from django.conf import settings
from django.db import models


class SolicitacaoApoio(models.Model):
    class Especialidade(models.TextChoices):
        NEUROPSICOLOGIA = "neuropsicologia", "Neuropsicólogo"
        ASSISTENCIA_SOCIAL = "assistencia_social", "Assistente Social"
        SEGURANCA_TRABALHO = "seguranca_trabalho", "Segurança do Trabalho"

    class Estado(models.TextChoices):
        ABERTA = "aberta", "Aguardando resposta"
        RESPONDIDA = "respondida", "Respondida"

    servidor_sismed_id = models.IntegerField(db_index=True)
    protocolo_sismed_id = models.IntegerField(null=True, blank=True)
    especialidade = models.CharField(max_length=20, choices=Especialidade.choices)
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="solicitacoes_apoio_feitas",
    )
    unidade = models.ForeignKey(
        "contas.Unidade",
        on_delete=models.PROTECT,
        related_name="solicitacoes_apoio",
    )
    texto_solicitacao = models.TextField()
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.ABERTA)
    respondente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="solicitacoes_apoio_respondidas",
    )
    texto_resposta = models.TextField(blank=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    respondido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-criado_em",)


class EventoSolicitacaoApoio(models.Model):
    class Acao(models.TextChoices):
        CRIADA = "criada", "Solicitação criada"
        RESPONDIDA = "respondida", "Solicitação respondida"

    solicitacao = models.ForeignKey(
        SolicitacaoApoio, on_delete=models.CASCADE, related_name="eventos"
    )
    ator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    acao = models.CharField(max_length=12, choices=Acao.choices)
    estado_anterior = models.CharField(max_length=12, blank=True)
    estado_novo = models.CharField(max_length=12)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-criado_em",)
