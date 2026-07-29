from django.conf import settings
from django.db import models


class Parecer(models.Model):
    class Conclusao(models.TextChoices):
        APTO = "apto", "Apto para o trabalho"
        AFASTAMENTO = "afastamento", "Necessita afastamento"
        ENCAMINHAMENTO = "encaminhamento", "Necessita encaminhamento"
        ACOMPANHAMENTO = "acompanhamento", "Manter em acompanhamento"

    class Estado(models.TextChoices):
        RASCUNHO = "rascunho", "Rascunho"
        CONCLUIDO = "concluido", "Concluído"

    servidor_sismed_id = models.IntegerField(db_index=True)
    protocolo_sismed_id = models.IntegerField(null=True, blank=True)
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pareceres",
    )
    unidade = models.ForeignKey(
        "contas.Unidade",
        on_delete=models.PROTECT,
        related_name="pareceres",
    )
    texto = models.TextField()
    conclusao = models.CharField(max_length=20, choices=Conclusao.choices)
    estado = models.CharField(max_length=12, choices=Estado.choices, default=Estado.RASCUNHO)
    prioritario = models.BooleanField(default=False)
    data_reavaliacao = models.DateField(null=True, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    concluido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-criado_em",)


class EventoParecer(models.Model):
    class Acao(models.TextChoices):
        CRIADO = "criado", "Parecer criado"
        ATUALIZADO = "atualizado", "Parecer atualizado"
        CONCLUIDO = "concluido", "Parecer concluído"

    parecer = models.ForeignKey(Parecer, on_delete=models.CASCADE, related_name="eventos")
    ator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    acao = models.CharField(max_length=12, choices=Acao.choices)
    estado_anterior = models.CharField(max_length=12, blank=True)
    estado_novo = models.CharField(max_length=12)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-criado_em",)
