import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.legado.models import Servidor
from apps.pareceres.models import EventoParecer, Parecer


def _validar_servidor(servidor_sismed_id: int) -> None:
    if not Servidor.objects.filter(cd_servidor=servidor_sismed_id).exists():
        raise ValidationError("O servidor informado não existe no SisMed.")


def _pode_alterar(*, ator, parecer: Parecer) -> bool:
    return parecer.autor_id == ator.pk or ator.is_superuser


def _registrar_evento(
    *,
    parecer: Parecer,
    ator,
    acao: str,
    estado_anterior: str,
) -> EventoParecer:
    return EventoParecer.objects.create(
        parecer=parecer,
        ator=ator,
        acao=acao,
        estado_anterior=estado_anterior,
        estado_novo=parecer.estado,
    )


@transaction.atomic
def criar_parecer(
    *,
    ator,
    servidor_sismed_id: int,
    protocolo_sismed_id: int | None,
    texto: str,
    conclusao: str,
    prioritario: bool,
    data_reavaliacao: datetime.date | None,
    concluir: bool,
) -> Parecer:
    _validar_servidor(servidor_sismed_id)
    if conclusao not in Parecer.Conclusao.values:
        raise ValidationError("A conclusão informada não é válida.")
    if not texto.strip():
        raise ValidationError("O parecer não pode ficar em branco.")

    parecer = Parecer(
        servidor_sismed_id=servidor_sismed_id,
        protocolo_sismed_id=protocolo_sismed_id,
        autor=ator,
        unidade=ator.unidade,
        texto=texto.strip(),
        conclusao=conclusao,
        prioritario=prioritario,
        data_reavaliacao=data_reavaliacao,
    )
    if concluir:
        parecer.estado = Parecer.Estado.CONCLUIDO
        parecer.concluido_em = timezone.now()
    parecer.full_clean()
    parecer.save()
    _registrar_evento(
        parecer=parecer,
        ator=ator,
        acao=EventoParecer.Acao.CRIADO,
        estado_anterior="",
    )
    return parecer


@transaction.atomic
def atualizar_parecer(
    *,
    ator,
    parecer: Parecer,
    texto: str,
    conclusao: str,
    prioritario: bool,
    data_reavaliacao: datetime.date | None,
) -> Parecer:
    if parecer.estado != Parecer.Estado.RASCUNHO:
        raise ValidationError("Somente um parecer em rascunho pode ser editado.")
    if not _pode_alterar(ator=ator, parecer=parecer):
        raise ValidationError("Somente o autor pode editar este parecer.")
    if conclusao not in Parecer.Conclusao.values:
        raise ValidationError("A conclusão informada não é válida.")
    if not texto.strip():
        raise ValidationError("O parecer não pode ficar em branco.")

    parecer.texto = texto.strip()
    parecer.conclusao = conclusao
    parecer.prioritario = prioritario
    parecer.data_reavaliacao = data_reavaliacao
    parecer.full_clean()
    parecer.save()
    _registrar_evento(
        parecer=parecer,
        ator=ator,
        acao=EventoParecer.Acao.ATUALIZADO,
        estado_anterior=Parecer.Estado.RASCUNHO,
    )
    return parecer


@transaction.atomic
def concluir_parecer(*, ator, parecer: Parecer) -> Parecer:
    if parecer.estado != Parecer.Estado.RASCUNHO:
        raise ValidationError("Este parecer já foi concluído.")
    if not _pode_alterar(ator=ator, parecer=parecer):
        raise ValidationError("Somente o autor pode concluir este parecer.")

    estado_anterior = parecer.estado
    parecer.estado = Parecer.Estado.CONCLUIDO
    parecer.concluido_em = timezone.now()
    parecer.save(update_fields=("estado", "concluido_em"))
    _registrar_evento(
        parecer=parecer,
        ator=ator,
        acao=EventoParecer.Acao.CONCLUIDO,
        estado_anterior=estado_anterior,
    )
    return parecer
