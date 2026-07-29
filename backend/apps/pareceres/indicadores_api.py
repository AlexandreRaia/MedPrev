import datetime

from ninja import Router, Schema
from ninja.security import django_auth

from apps.contas.api import exigir_permissao
from apps.contas.permissions import VISUALIZAR_INDICADORES_GERENCIAIS
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


@router.get("", response=IndicadoresSaida)
def consultar_indicadores(request):
    exigir_permissao(request, VISUALIZAR_INDICADORES_GERENCIAIS)

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

    return IndicadoresSaida(
        servidores_acompanhados=Parecer.objects.values("servidor_sismed_id").distinct().count(),
        pericias_60_dias=len(pericias_recentes),
        pareceres_em_rascunho=Parecer.objects.filter(estado=Parecer.Estado.RASCUNHO).count(),
        pericias_com_atestado_60_dias=sum(
            1 for pericia in pericias_recentes if pericia.ic_atestado == "t"
        ),
        grupos_cid=grupos_cid,
    )
