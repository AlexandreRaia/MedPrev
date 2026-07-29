from collections.abc import Iterable

from django.db.models import Q, QuerySet

from apps.legado.models import (
    Pericia,
    Protocolo,
    ProtocoloCid,
    Servidor,
    SituacaoProtocolo,
)

LIMITE_PADRAO_BUSCA = 20
LIMITE_MAXIMO_BUSCA = 100


def buscar_servidores(
    termo: str,
    *,
    limite: int = LIMITE_PADRAO_BUSCA,
) -> QuerySet[Servidor]:
    """
    Busca por nome, nome social, CPF ou prontuário.

    Uma busca vazia nunca retorna todo o cadastro. O limite também é restringido
    para evitar leituras acidentais muito grandes no banco legado.
    """

    termo_normalizado = termo.strip()
    queryset = Servidor.objects.all()

    if not termo_normalizado:
        return queryset.none()

    filtros = (
        Q(nm_servidor__icontains=termo_normalizado)
        | Q(nm_social__icontains=termo_normalizado)
        | Q(nro_cpf__icontains=termo_normalizado)
    )

    codigo_prontuario = termo_normalizado
    if codigo_prontuario[:1].lower() == "p":
        codigo_prontuario = codigo_prontuario[1:]
    if codigo_prontuario.isdecimal():
        filtros |= Q(cd_servidor=int(codigo_prontuario))

    limite_seguro = max(1, min(limite, LIMITE_MAXIMO_BUSCA))
    return queryset.filter(filtros).order_by("nm_servidor", "cd_servidor")[:limite_seguro]


def protocolos_do_servidor(servidor_id: int) -> QuerySet[Protocolo]:
    """Retorna todos os protocolos, inclusive inativos ou cancelados."""

    return Protocolo.objects.filter(cd_servidor=servidor_id).order_by(
        "-dt_protocolo", "-cd_protocolo"
    )


def pericias_do_protocolo(protocolo_id: int) -> QuerySet[Pericia]:
    """Retorna as perícias associadas ao protocolo informado."""

    return Pericia.objects.filter(cd_protocolo=protocolo_id).order_by("-dt_pericia", "-cd_pericia")


def protocolos_mais_recentes_por_servidor(
    servidor_ids: Iterable[int],
) -> dict[int, Protocolo]:
    """Mapeia cada servidor ao seu protocolo mais recente, quando existir."""

    ids = {servidor_id for servidor_id in servidor_ids if servidor_id is not None}
    if not ids:
        return {}

    mais_recentes: dict[int, Protocolo] = {}
    protocolos = Protocolo.objects.filter(cd_servidor__in=ids).order_by(
        "cd_servidor", "-dt_protocolo", "-cd_protocolo"
    )
    for protocolo in protocolos:
        mais_recentes.setdefault(protocolo.cd_servidor, protocolo)
    return mais_recentes


def cids_por_protocolo(protocolo_ids: Iterable[int]) -> dict[int, list[str]]:
    """Mapeia cada protocolo aos códigos de CID associados."""

    ids = {protocolo_id for protocolo_id in protocolo_ids if protocolo_id is not None}
    if not ids:
        return {}

    agrupado: dict[int, list[str]] = {}
    pares = ProtocoloCid.objects.filter(cd_protocolo__in=ids).values_list("cd_protocolo", "cd_cid")
    for cd_protocolo, cd_cid in pares:
        agrupado.setdefault(cd_protocolo, []).append(cd_cid)
    return agrupado


def descricoes_das_situacoes(situacao_ids: Iterable[int]) -> dict[int, str]:
    """Mapeia códigos de situação de protocolo para sua descrição."""

    ids = {situacao_id for situacao_id in situacao_ids if situacao_id is not None}
    if not ids:
        return {}
    return dict(
        SituacaoProtocolo.objects.filter(cd_situacaoprotocolo__in=ids).values_list(
            "cd_situacaoprotocolo", "ds_situacaoprotocolo"
        )
    )
