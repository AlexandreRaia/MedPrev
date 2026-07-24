from django.db.models import Q, QuerySet

from apps.legado.models import Pericia, Protocolo, Servidor

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

    if termo_normalizado.isdecimal():
        filtros |= Q(cd_servidor=int(termo_normalizado))

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
