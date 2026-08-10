import datetime

from ninja import Router, Schema
from ninja.security import django_auth

from apps.apoio.models import SolicitacaoApoio
from apps.contas.permissions import (
    RESPONDER_SOLICITACAO_APOIO,
    SOLICITAR_APOIO_ESPECIALIZADO,
    nome_completo_da_permissao,
)
from apps.legado.models import Pericia
from apps.legado.selectors import cids_por_protocolo
from apps.pareceres.models import Parecer

router = Router(tags=["Indicadores"], auth=django_auth)

JANELA_EM_DIAS = 60


class GrupoCidIndicador(Schema):
    codigo: str
    ocorrencias: int


class IndicadoresSaida(Schema):
    servidores_acompanhados: int
    pericias_60_dias: int
    pareceres_em_rascunho: int
    pericias_com_atestado_60_dias: int
    grupos_cid: list[GrupoCidIndicador]
    solicitacoes_apoio_abertas: int
    minhas_solicitacoes_pendentes: int | None
    pareceres_concluidos: int
    solicitacoes_apoio_respondidas: int


def _tem_permissao(request, codename: str) -> bool:
    return request.user.has_perm(nome_completo_da_permissao(codename))


@router.get("", response=IndicadoresSaida)
def consultar_indicadores(request):
    """
    Os indicadores são agregados e não identificam nenhum servidor
    individualmente, então qualquer perfil autenticado pode consultá-los, e a
    Visão Geral mostra o sistema inteiro — sem escopo por unidade. A Consulta
    já permite localizar qualquer servidor independente da unidade de quem
    procura, então restringir só o painel agregado não protegia nada, apenas
    mostrava uma fatia incompleta. Só `minhas_solicitacoes_pendentes` continua
    pessoal, porque é sobre o que o próprio usuário tem para fazer.
    """

    pareceres = Parecer.objects.all()
    solicitacoes = SolicitacaoApoio.objects.all()

    limite = datetime.date.today() - datetime.timedelta(days=JANELA_EM_DIAS)
    pericias_recentes = list(Pericia.objects.filter(dt_pericia__gte=limite))

    cids = cids_por_protocolo(pericia.cd_protocolo for pericia in pericias_recentes)
    contagem_por_cid: dict[str, int] = {}
    for pericia in pericias_recentes:
        for codigo in cids.get(pericia.cd_protocolo, []):
            contagem_por_cid[codigo] = contagem_por_cid.get(codigo, 0) + 1
    grupos_cid = sorted(
        (
            GrupoCidIndicador(codigo=codigo, ocorrencias=total)
            for codigo, total in contagem_por_cid.items()
        ),
        key=lambda grupo: grupo.ocorrencias,
        reverse=True,
    )

    minhas_solicitacoes_pendentes: int | None = None
    if _tem_permissao(request, RESPONDER_SOLICITACAO_APOIO):
        grupos_do_usuario = set(request.user.groups.values_list("name", flat=True))
        especialidades_do_usuario = [
            codigo
            for codigo, descricao in SolicitacaoApoio.Especialidade.choices
            if descricao in grupos_do_usuario
        ]
        minhas_solicitacoes_pendentes = SolicitacaoApoio.objects.filter(
            estado=SolicitacaoApoio.Estado.ABERTA,
            especialidade__in=especialidades_do_usuario,
        ).count()
    elif _tem_permissao(request, SOLICITAR_APOIO_ESPECIALIZADO):
        minhas_solicitacoes_pendentes = SolicitacaoApoio.objects.filter(
            estado=SolicitacaoApoio.Estado.ABERTA,
            solicitante=request.user,
        ).count()

    return IndicadoresSaida(
        servidores_acompanhados=pareceres.values("servidor_sismed_id").distinct().count(),
        pericias_60_dias=len(pericias_recentes),
        pareceres_em_rascunho=pareceres.filter(estado=Parecer.Estado.RASCUNHO).count(),
        pericias_com_atestado_60_dias=sum(
            1 for pericia in pericias_recentes if pericia.ic_atestado == "t"
        ),
        grupos_cid=grupos_cid,
        solicitacoes_apoio_abertas=solicitacoes.filter(
            estado=SolicitacaoApoio.Estado.ABERTA
        ).count(),
        minhas_solicitacoes_pendentes=minhas_solicitacoes_pendentes,
        pareceres_concluidos=pareceres.filter(estado=Parecer.Estado.CONCLUIDO).count(),
        solicitacoes_apoio_respondidas=solicitacoes.filter(
            estado=SolicitacaoApoio.Estado.RESPONDIDA
        ).count(),
    )
