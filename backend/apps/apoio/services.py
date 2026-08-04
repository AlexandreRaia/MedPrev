from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.apoio.models import EventoSolicitacaoApoio, SolicitacaoApoio
from apps.legado.models import Servidor


def _validar_servidor(servidor_sismed_id: int) -> None:
    if not Servidor.objects.filter(cd_servidor=servidor_sismed_id).exists():
        raise ValidationError("O servidor informado não existe no SisMed.")


def _registrar_evento(
    *,
    solicitacao: SolicitacaoApoio,
    ator,
    acao: str,
    estado_anterior: str,
) -> EventoSolicitacaoApoio:
    return EventoSolicitacaoApoio.objects.create(
        solicitacao=solicitacao,
        ator=ator,
        acao=acao,
        estado_anterior=estado_anterior,
        estado_novo=solicitacao.estado,
    )


@transaction.atomic
def criar_solicitacao(
    *,
    ator,
    servidor_sismed_id: int,
    protocolo_sismed_id: int | None,
    especialidade: str,
    texto_solicitacao: str,
) -> SolicitacaoApoio:
    _validar_servidor(servidor_sismed_id)
    if especialidade not in SolicitacaoApoio.Especialidade.values:
        raise ValidationError("A especialidade informada não é válida.")
    if not texto_solicitacao.strip():
        raise ValidationError("A solicitação não pode ficar em branco.")

    solicitacao = SolicitacaoApoio(
        servidor_sismed_id=servidor_sismed_id,
        protocolo_sismed_id=protocolo_sismed_id,
        especialidade=especialidade,
        solicitante=ator,
        unidade=ator.unidade,
        texto_solicitacao=texto_solicitacao.strip(),
    )
    solicitacao.full_clean()
    solicitacao.save()
    _registrar_evento(
        solicitacao=solicitacao,
        ator=ator,
        acao=EventoSolicitacaoApoio.Acao.CRIADA,
        estado_anterior="",
    )
    return solicitacao


@transaction.atomic
def responder_solicitacao(
    *,
    ator,
    solicitacao: SolicitacaoApoio,
    texto_resposta: str,
) -> SolicitacaoApoio:
    if solicitacao.estado != SolicitacaoApoio.Estado.ABERTA:
        raise ValidationError("Esta solicitação já foi respondida.")
    if not ator.groups.filter(name=solicitacao.get_especialidade_display()).exists():
        raise ValidationError("Somente um profissional da especialidade solicitada pode responder.")
    if not texto_resposta.strip():
        raise ValidationError("A resposta não pode ficar em branco.")

    estado_anterior = solicitacao.estado
    solicitacao.respondente = ator
    solicitacao.texto_resposta = texto_resposta.strip()
    solicitacao.estado = SolicitacaoApoio.Estado.RESPONDIDA
    solicitacao.respondido_em = timezone.now()
    solicitacao.save(update_fields=("respondente", "texto_resposta", "estado", "respondido_em"))
    _registrar_evento(
        solicitacao=solicitacao,
        ator=ator,
        acao=EventoSolicitacaoApoio.Acao.RESPONDIDA,
        estado_anterior=estado_anterior,
    )
    return solicitacao
