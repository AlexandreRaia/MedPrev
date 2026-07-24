from typing import Any

from django.contrib.auth import (
    authenticate,
    login,
    logout,
    update_session_auth_hash,
)
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.middleware.csrf import get_token
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth
from ninja.utils import check_csrf
from pydantic import Field

from apps.contas.models import EventoAutenticacao, Usuario
from apps.contas.permissions import (
    GERENCIAR_ACESSOS,
    PERFIS_E_PERMISSOES,
    PERMISSOES_DE_NEGOCIO,
    nome_completo_da_permissao,
)
from apps.contas.services import alterar_propria_senha, registrar_evento_autenticacao

router = Router(tags=["Autenticação"])


class LoginEntrada(Schema):
    usuario: str = Field(min_length=1, max_length=150)
    senha: str = Field(min_length=1, max_length=128)


class UsuarioSessaoSaida(Schema):
    id: int
    usuario: str
    nome: str
    email: str
    grupos: list[str]
    permissoes: list[str]
    superusuario: bool
    deve_trocar_senha: bool
    unidade: dict[str, int | str]


class CsrfSaida(Schema):
    csrf_token: str


class MensagemSaida(Schema):
    mensagem: str


class AlterarSenhaEntrada(Schema):
    senha_atual: str = Field(min_length=1, max_length=128)
    nova_senha: str = Field(min_length=8, max_length=128)


class PerfilSaida(Schema):
    nome: str
    permissoes: list[str]


def serializar_usuario(usuario: Usuario) -> UsuarioSessaoSaida:
    permissoes = [
        codename
        for codename, _ in PERMISSOES_DE_NEGOCIO
        if usuario.has_perm(nome_completo_da_permissao(codename))
    ]
    return UsuarioSessaoSaida(
        id=usuario.pk,
        usuario=usuario.get_username(),
        nome=usuario.get_full_name() or usuario.get_username(),
        email=usuario.email,
        grupos=list(usuario.groups.order_by("name").values_list("name", flat=True)),
        permissoes=permissoes,
        superusuario=usuario.is_superuser,
        deve_trocar_senha=usuario.deve_trocar_senha,
        unidade={
            "id": usuario.unidade_id,
            "codigo": usuario.unidade.codigo,
            "nome": usuario.unidade.nome,
        },
    )


def exigir_permissao(request: Any, codename: str) -> None:
    if not request.user.has_perm(nome_completo_da_permissao(codename)):
        raise HttpError(403, "Você não possui permissão para esta ação.")


def verificar_csrf(request: Any) -> None:
    if check_csrf(request):
        raise HttpError(403, "Falha na validação CSRF.")


@router.get(
    "/csrf",
    response=CsrfSaida,
    auth=None,
    summary="Obter token CSRF",
)
def obter_csrf(request) -> CsrfSaida:
    return CsrfSaida(csrf_token=get_token(request))


@router.post(
    "/login",
    response=UsuarioSessaoSaida,
    auth=None,
    summary="Iniciar sessão",
)
def entrar(request, dados: LoginEntrada) -> UsuarioSessaoSaida:
    verificar_csrf(request)
    identificador = dados.usuario.strip()
    usuario = authenticate(
        request,
        username=identificador,
        password=dados.senha,
    )
    if usuario is None:
        registrar_evento_autenticacao(
            EventoAutenticacao.Tipo.LOGIN_FALHA,
            identificador=identificador,
        )
        raise HttpError(401, "Usuário ou senha inválidos.")

    login(request, usuario)
    registrar_evento_autenticacao(
        EventoAutenticacao.Tipo.LOGIN_SUCESSO,
        usuario=usuario,
        identificador=usuario.get_username(),
    )
    return serializar_usuario(usuario)


@router.post(
    "/logout",
    response=MensagemSaida,
    auth=django_auth,
    summary="Encerrar sessão",
)
def sair(request) -> MensagemSaida:
    usuario = request.user
    registrar_evento_autenticacao(
        EventoAutenticacao.Tipo.LOGOUT,
        usuario=usuario,
        identificador=usuario.get_username(),
    )
    logout(request)
    return MensagemSaida(mensagem="Sessão encerrada.")


@router.get(
    "/me",
    response=UsuarioSessaoSaida,
    auth=django_auth,
    summary="Consultar sessão atual",
)
def sessao_atual(request) -> UsuarioSessaoSaida:
    return serializar_usuario(request.user)


@router.post(
    "/alterar-senha",
    response=MensagemSaida,
    auth=django_auth,
    summary="Alterar a própria senha",
)
def alterar_senha(request, dados: AlterarSenhaEntrada) -> MensagemSaida:
    try:
        alterar_propria_senha(
            usuario=request.user,
            senha_atual=dados.senha_atual,
            nova_senha=dados.nova_senha,
        )
        update_session_auth_hash(request, request.user)
    except ValidationError as exc:
        raise HttpError(400, "; ".join(exc.messages)) from exc
    return MensagemSaida(mensagem="Senha alterada com sucesso.")


@router.get(
    "/matriz",
    response=list[PerfilSaida],
    auth=django_auth,
    summary="Consultar matriz inicial de acesso",
)
def consultar_matriz(request) -> list[PerfilSaida]:
    exigir_permissao(request, GERENCIAR_ACESSOS)
    grupos = {
        grupo.name: set(
            grupo.permissions.filter(
                content_type__app_label="contas",
                content_type__model="usuario",
            ).values_list("codename", flat=True)
        )
        for grupo in Group.objects.filter(name__in=PERFIS_E_PERMISSOES)
        .prefetch_related("permissions")
    }
    return [
        PerfilSaida(
            nome=nome,
            permissoes=[
                codename
                for codename, _ in PERMISSOES_DE_NEGOCIO
                if codename in grupos.get(nome, set())
            ],
        )
        for nome in PERFIS_E_PERMISSOES
    ]
