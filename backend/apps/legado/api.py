from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.security import django_auth

from apps.contas.api import exigir_permissao
from apps.contas.permissions import (
    CONSULTAR_CONTEUDO_MEDICO,
    CONSULTAR_DADOS,
    nome_completo_da_permissao,
)
from apps.legado.models import Pericia, Servidor
from apps.legado.selectors import (
    buscar_servidores,
    descricoes_das_situacoes,
    pericias_do_protocolo,
    protocolos_do_servidor,
)

router = Router(tags=["Legado"], auth=django_auth)


class ServidorResumoSaida(Schema):
    id: int
    nome: str
    nome_social: str | None
    cpf: str | None
    email: str | None
    ativo: bool | None
    admissao: str | None


class ProtocoloResumoSaida(Schema):
    id: int
    data: str | None
    situacao: str | None


class PericiaResumoSaida(Schema):
    id: int
    protocolo_id: int
    data: str | None
    motivo: str | None
    subjetivo: str | None
    objetivo: str | None
    conduta: str | None
    relatorio: str | None
    atestado: bool
    dias_atestado: int | None


class ServidorDetalheSaida(ServidorResumoSaida):
    nascimento: str | None
    telefone: str | None
    celular: str | None
    protocolos: list[ProtocoloResumoSaida]
    historico_medico_visivel: bool
    pericias: list[PericiaResumoSaida]


def _serializar_resumo(servidor: Servidor) -> ServidorResumoSaida:
    return ServidorResumoSaida(
        id=servidor.cd_servidor,
        nome=servidor.nm_servidor,
        nome_social=servidor.nm_social,
        cpf=servidor.nro_cpf,
        email=servidor.ds_email,
        ativo=servidor.st_ativo,
        admissao=servidor.dt_admissao.isoformat() if servidor.dt_admissao else None,
    )


def _serializar_pericia(pericia: Pericia) -> PericiaResumoSaida:
    return PericiaResumoSaida(
        id=pericia.cd_pericia,
        protocolo_id=pericia.cd_protocolo,
        data=pericia.dt_pericia.isoformat() if pericia.dt_pericia else None,
        motivo=pericia.ds_pericia,
        subjetivo=pericia.ds_subjetivo,
        objetivo=pericia.ds_objetivo,
        conduta=pericia.ds_conduta,
        relatorio=pericia.ds_relatoriomedico,
        atestado=pericia.ic_atestado == "t",
        dias_atestado=pericia.qt_atestadodias,
    )


@router.get("/servidores", response=list[ServidorResumoSaida])
def listar_servidores(request, busca: str = ""):
    exigir_permissao(request, CONSULTAR_DADOS)
    servidores = buscar_servidores(busca)
    return [_serializar_resumo(servidor) for servidor in servidores]


@router.get("/servidores/{servidor_id}", response=ServidorDetalheSaida)
def consultar_servidor(request, servidor_id: int):
    exigir_permissao(request, CONSULTAR_DADOS)
    servidor = get_object_or_404(Servidor, pk=servidor_id)
    protocolos = list(protocolos_do_servidor(servidor_id))
    situacoes = descricoes_das_situacoes(protocolo.cd_situacaoprotocolo for protocolo in protocolos)

    pode_ver_historico_medico = request.user.has_perm(
        nome_completo_da_permissao(CONSULTAR_CONTEUDO_MEDICO)
    )
    pericias: list[PericiaResumoSaida] = []
    if pode_ver_historico_medico:
        for protocolo in protocolos:
            pericias.extend(
                _serializar_pericia(pericia)
                for pericia in pericias_do_protocolo(protocolo.cd_protocolo)
            )

    resumo = _serializar_resumo(servidor)
    return ServidorDetalheSaida(
        **resumo.model_dump(),
        nascimento=servidor.dt_nascimento.isoformat() if servidor.dt_nascimento else None,
        telefone=servidor.nro_telefone,
        celular=servidor.nro_celular,
        protocolos=[
            ProtocoloResumoSaida(
                id=protocolo.cd_protocolo,
                data=protocolo.dt_protocolo.isoformat() if protocolo.dt_protocolo else None,
                situacao=situacoes.get(protocolo.cd_situacaoprotocolo),
            )
            for protocolo in protocolos
        ],
        historico_medico_visivel=pode_ver_historico_medico,
        pericias=pericias,
    )
