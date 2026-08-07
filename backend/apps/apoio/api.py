from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth
from pydantic import Field

from apps.apoio.models import SolicitacaoApoio
from apps.apoio.services import criar_solicitacao, responder_solicitacao
from apps.contas.api import exigir_permissao
from apps.contas.permissions import (
    CONSULTAR_CONTEUDO_MEDICO,
    RESPONDER_SOLICITACAO_APOIO,
    SOLICITAR_APOIO_ESPECIALIZADO,
    VISUALIZAR_DADOS_GLOBAIS,
    nome_completo_da_permissao,
)
from apps.legado.models import Servidor
from apps.legado.selectors import descricoes_das_situacoes, protocolos_mais_recentes_por_servidor
from apps.pareceres.models import Parecer

router = Router(tags=["Apoio"], auth=django_auth)


class SolicitacaoApoioSaida(Schema):
    id: int
    servidor_sismed_id: int
    protocolo_sismed_id: int | None
    especialidade: str
    especialidade_descricao: str
    solicitante: str
    solicitante_id: int
    unidade: str
    texto_solicitacao: str
    estado: str
    estado_descricao: str
    respondente: str | None
    texto_resposta: str
    criado_em: str
    respondido_em: str | None


class MinhaSolicitacaoSaida(SolicitacaoApoioSaida):
    servidor_nome: str | None


class ApoioPorEspecialidadeSaida(Schema):
    especialidade: str
    especialidade_descricao: str
    estado: str
    estado_descricao: str


class AtendimentoAbertoSaida(Schema):
    servidor_sismed_id: int
    servidor_nome: str | None
    situacao_protocolo: str | None
    parecer_em_aberto: bool
    parecer_autor: str | None
    apoios: list[ApoioPorEspecialidadeSaida]
    ultima_atividade_em: str


class SolicitacaoApoioCriarEntrada(Schema):
    servidor_sismed_id: int
    protocolo_sismed_id: int | None = None
    especialidade: str
    texto_solicitacao: str = Field(min_length=1, max_length=4000)


class SolicitacaoApoioResponderEntrada(Schema):
    texto_resposta: str = Field(min_length=1, max_length=4000)


def _erro_validacao(exc: ValidationError) -> HttpError:
    mensagem = "; ".join(exc.messages)
    return HttpError(400, mensagem)


def _serializar(solicitacao: SolicitacaoApoio) -> SolicitacaoApoioSaida:
    return SolicitacaoApoioSaida(
        id=solicitacao.pk,
        servidor_sismed_id=solicitacao.servidor_sismed_id,
        protocolo_sismed_id=solicitacao.protocolo_sismed_id,
        especialidade=solicitacao.especialidade,
        especialidade_descricao=solicitacao.get_especialidade_display(),
        solicitante=(
            solicitacao.solicitante.get_full_name() or solicitacao.solicitante.get_username()
        ),
        solicitante_id=solicitacao.solicitante_id,
        unidade=solicitacao.unidade.nome,
        texto_solicitacao=solicitacao.texto_solicitacao,
        estado=solicitacao.estado,
        estado_descricao=solicitacao.get_estado_display(),
        respondente=(
            (solicitacao.respondente.get_full_name() or solicitacao.respondente.get_username())
            if solicitacao.respondente_id
            else None
        ),
        texto_resposta=solicitacao.texto_resposta,
        criado_em=solicitacao.criado_em.isoformat(),
        respondido_em=(
            solicitacao.respondido_em.isoformat() if solicitacao.respondido_em else None
        ),
    )


@router.post("", response={201: SolicitacaoApoioSaida})
def cadastrar_solicitacao(request, dados: SolicitacaoApoioCriarEntrada):
    exigir_permissao(request, SOLICITAR_APOIO_ESPECIALIZADO)
    try:
        solicitacao = criar_solicitacao(
            ator=request.user,
            servidor_sismed_id=dados.servidor_sismed_id,
            protocolo_sismed_id=dados.protocolo_sismed_id,
            especialidade=dados.especialidade,
            texto_solicitacao=dados.texto_solicitacao,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return 201, _serializar(solicitacao)


@router.get("", response=list[SolicitacaoApoioSaida])
def listar_solicitacoes(request, servidor_sismed_id: int):
    exigir_permissao(request, CONSULTAR_CONTEUDO_MEDICO)
    solicitacoes = SolicitacaoApoio.objects.filter(
        servidor_sismed_id=servidor_sismed_id
    ).select_related("solicitante", "respondente", "unidade")
    return [_serializar(solicitacao) for solicitacao in solicitacoes]


@router.get("/minhas", response=list[MinhaSolicitacaoSaida])
def listar_minhas_solicitacoes(request):
    exigir_permissao(request, RESPONDER_SOLICITACAO_APOIO)
    grupos_do_usuario = set(request.user.groups.values_list("name", flat=True))
    especialidades_do_usuario = [
        codigo
        for codigo, descricao in SolicitacaoApoio.Especialidade.choices
        if descricao in grupos_do_usuario
    ]
    solicitacoes = list(
        SolicitacaoApoio.objects.filter(
            estado=SolicitacaoApoio.Estado.ABERTA,
            especialidade__in=especialidades_do_usuario,
        ).select_related("solicitante", "unidade")
    )
    nomes_dos_servidores = dict(
        Servidor.objects.filter(
            cd_servidor__in={solicitacao.servidor_sismed_id for solicitacao in solicitacoes}
        ).values_list("cd_servidor", "nm_servidor")
    )
    return [
        MinhaSolicitacaoSaida(
            **_serializar(solicitacao).model_dump(),
            servidor_nome=nomes_dos_servidores.get(solicitacao.servidor_sismed_id),
        )
        for solicitacao in solicitacoes
    ]


@router.post("/{solicitacao_id}/responder", response=SolicitacaoApoioSaida)
def responder(request, solicitacao_id: int, dados: SolicitacaoApoioResponderEntrada):
    exigir_permissao(request, RESPONDER_SOLICITACAO_APOIO)
    solicitacao = get_object_or_404(SolicitacaoApoio, pk=solicitacao_id)
    try:
        solicitacao = responder_solicitacao(
            ator=request.user,
            solicitacao=solicitacao,
            texto_resposta=dados.texto_resposta,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return _serializar(solicitacao)


def _apoios_por_especialidade(
    solicitacoes_do_servidor: list[SolicitacaoApoio],
) -> list[ApoioPorEspecialidadeSaida]:
    """
    Um selo por especialidade já solicitada para o servidor — em paralelo, sem
    ordem entre elas. Se houver mais de uma solicitação da mesma especialidade,
    uma ainda aberta tem prioridade sobre uma já respondida.
    """
    por_especialidade: dict[str, list[SolicitacaoApoio]] = {}
    for solicitacao in solicitacoes_do_servidor:
        por_especialidade.setdefault(solicitacao.especialidade, []).append(solicitacao)

    apoios = []
    for especialidade, _descricao in SolicitacaoApoio.Especialidade.choices:
        solicitacoes = por_especialidade.get(especialidade)
        if not solicitacoes:
            continue
        estado = (
            SolicitacaoApoio.Estado.ABERTA
            if any(s.estado == SolicitacaoApoio.Estado.ABERTA for s in solicitacoes)
            else SolicitacaoApoio.Estado.RESPONDIDA
        )
        apoios.append(
            ApoioPorEspecialidadeSaida(
                especialidade=especialidade,
                especialidade_descricao=solicitacoes[0].get_especialidade_display(),
                estado=estado,
                estado_descricao=SolicitacaoApoio.Estado(estado).label,
            )
        )
    return apoios


@router.get("/atendimentos", response=list[AtendimentoAbertoSaida])
def listar_atendimentos(request):
    """
    Casos em andamento: um parecer em rascunho e/ou uma solicitação de apoio
    ainda sem resposta. Não é filtrado por autor — um colega que assuma o
    atendimento precisa enxergar o que já está pendente, não só o que ele
    mesmo abriu. Escopado pela unidade do usuário, a menos que ele tenha
    visão global. Some da lista quando o parecer é concluído e não sobra
    nenhuma solicitação em aberto — o histórico continua acessível pela
    Consulta.
    """
    exigir_permissao(request, SOLICITAR_APOIO_ESPECIALIZADO)

    pareceres_em_rascunho_query = Parecer.objects.filter(
        estado=Parecer.Estado.RASCUNHO
    ).select_related("autor")
    solicitacoes_query = SolicitacaoApoio.objects.all()
    if not request.user.has_perm(nome_completo_da_permissao(VISUALIZAR_DADOS_GLOBAIS)):
        pareceres_em_rascunho_query = pareceres_em_rascunho_query.filter(
            unidade=request.user.unidade
        )
        solicitacoes_query = solicitacoes_query.filter(unidade=request.user.unidade)

    pareceres_em_rascunho = list(pareceres_em_rascunho_query)
    solicitacoes = list(solicitacoes_query)

    servidor_ids = {parecer.servidor_sismed_id for parecer in pareceres_em_rascunho} | {
        solicitacao.servidor_sismed_id
        for solicitacao in solicitacoes
        if solicitacao.estado == SolicitacaoApoio.Estado.ABERTA
    }

    nomes_dos_servidores = dict(
        Servidor.objects.filter(cd_servidor__in=servidor_ids).values_list(
            "cd_servidor", "nm_servidor"
        )
    )
    protocolos_recentes = protocolos_mais_recentes_por_servidor(servidor_ids)
    situacoes_dos_protocolos = descricoes_das_situacoes(
        protocolo.cd_situacaoprotocolo for protocolo in protocolos_recentes.values()
    )

    resumos = []
    for servidor_id in servidor_ids:
        pareceres_do_servidor = [
            parecer
            for parecer in pareceres_em_rascunho
            if parecer.servidor_sismed_id == servidor_id
        ]
        solicitacoes_do_servidor = [
            solicitacao
            for solicitacao in solicitacoes
            if solicitacao.servidor_sismed_id == servidor_id
        ]
        datas = [parecer.atualizado_em for parecer in pareceres_do_servidor] + [
            solicitacao.respondido_em or solicitacao.criado_em
            for solicitacao in solicitacoes_do_servidor
        ]
        parecer_autor = None
        if pareceres_do_servidor:
            autor = pareceres_do_servidor[0].autor
            parecer_autor = autor.get_full_name() or autor.get_username()

        protocolo_recente = protocolos_recentes.get(servidor_id)
        situacao_protocolo = (
            situacoes_dos_protocolos.get(protocolo_recente.cd_situacaoprotocolo)
            if protocolo_recente
            else None
        )

        resumos.append(
            AtendimentoAbertoSaida(
                servidor_sismed_id=servidor_id,
                servidor_nome=nomes_dos_servidores.get(servidor_id),
                situacao_protocolo=situacao_protocolo,
                parecer_em_aberto=len(pareceres_do_servidor) > 0,
                parecer_autor=parecer_autor,
                apoios=_apoios_por_especialidade(solicitacoes_do_servidor),
                ultima_atividade_em=max(datas).isoformat(),
            )
        )

    resumos.sort(key=lambda resumo: resumo.ultima_atividade_em, reverse=True)
    return resumos
