from datetime import date

from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth
from pydantic import Field

from apps.contas.api import exigir_permissao
from apps.contas.permissions import ALTERAR_CONTEUDO_MEDICO, CONSULTAR_CONTEUDO_MEDICO
from apps.pareceres.models import Parecer
from apps.pareceres.services import atualizar_parecer, concluir_parecer, criar_parecer

router = Router(tags=["Pareceres"], auth=django_auth)


class ParecerSaida(Schema):
    id: int
    servidor_sismed_id: int
    protocolo_sismed_id: int | None
    autor: str
    autor_id: int
    unidade: str
    texto: str
    conclusao: str
    conclusao_descricao: str
    estado: str
    estado_descricao: str
    prioritario: bool
    data_reavaliacao: str | None
    criado_em: str
    atualizado_em: str
    concluido_em: str | None


class ParecerCriarEntrada(Schema):
    servidor_sismed_id: int
    protocolo_sismed_id: int | None = None
    texto: str = Field(min_length=1, max_length=4000)
    conclusao: str
    prioritario: bool = False
    data_reavaliacao: date | None = None
    concluir: bool = False


class ParecerAtualizarEntrada(Schema):
    texto: str = Field(min_length=1, max_length=4000)
    conclusao: str
    prioritario: bool = False
    data_reavaliacao: date | None = None


def _erro_validacao(exc: ValidationError) -> HttpError:
    mensagem = "; ".join(exc.messages)
    return HttpError(400, mensagem)


def _serializar(parecer: Parecer) -> ParecerSaida:
    return ParecerSaida(
        id=parecer.pk,
        servidor_sismed_id=parecer.servidor_sismed_id,
        protocolo_sismed_id=parecer.protocolo_sismed_id,
        autor=parecer.autor.get_full_name() or parecer.autor.get_username(),
        autor_id=parecer.autor_id,
        unidade=parecer.unidade.nome,
        texto=parecer.texto,
        conclusao=parecer.conclusao,
        conclusao_descricao=parecer.get_conclusao_display(),
        estado=parecer.estado,
        estado_descricao=parecer.get_estado_display(),
        prioritario=parecer.prioritario,
        data_reavaliacao=(
            parecer.data_reavaliacao.isoformat() if parecer.data_reavaliacao else None
        ),
        criado_em=parecer.criado_em.isoformat(),
        atualizado_em=parecer.atualizado_em.isoformat(),
        concluido_em=parecer.concluido_em.isoformat() if parecer.concluido_em else None,
    )


@router.get("", response=list[ParecerSaida])
def listar_pareceres(request, servidor_sismed_id: int):
    exigir_permissao(request, CONSULTAR_CONTEUDO_MEDICO)
    pareceres = Parecer.objects.filter(servidor_sismed_id=servidor_sismed_id).select_related(
        "autor", "unidade"
    )
    return [_serializar(parecer) for parecer in pareceres]


@router.post("", response={201: ParecerSaida})
def cadastrar_parecer(request, dados: ParecerCriarEntrada):
    exigir_permissao(request, ALTERAR_CONTEUDO_MEDICO)
    try:
        parecer = criar_parecer(
            ator=request.user,
            servidor_sismed_id=dados.servidor_sismed_id,
            protocolo_sismed_id=dados.protocolo_sismed_id,
            texto=dados.texto,
            conclusao=dados.conclusao,
            prioritario=dados.prioritario,
            data_reavaliacao=dados.data_reavaliacao,
            concluir=dados.concluir,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return 201, _serializar(parecer)


@router.patch("/{parecer_id}", response=ParecerSaida)
def editar_parecer(request, parecer_id: int, dados: ParecerAtualizarEntrada):
    exigir_permissao(request, ALTERAR_CONTEUDO_MEDICO)
    parecer = get_object_or_404(Parecer, pk=parecer_id)
    try:
        parecer = atualizar_parecer(
            ator=request.user,
            parecer=parecer,
            texto=dados.texto,
            conclusao=dados.conclusao,
            prioritario=dados.prioritario,
            data_reavaliacao=dados.data_reavaliacao,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return _serializar(parecer)


@router.post("/{parecer_id}/concluir", response=ParecerSaida)
def concluir(request, parecer_id: int):
    exigir_permissao(request, ALTERAR_CONTEUDO_MEDICO)
    parecer = get_object_or_404(Parecer, pk=parecer_id)
    try:
        parecer = concluir_parecer(ator=request.user, parecer=parecer)
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return _serializar(parecer)
