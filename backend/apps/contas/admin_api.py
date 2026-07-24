from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from ninja import Router, Schema
from ninja.errors import HttpError
from ninja.security import django_auth
from pydantic import Field

from apps.contas.api import exigir_permissao
from apps.contas.models import Unidade, Usuario
from apps.contas.permissions import GERENCIAR_ACESSOS, PERFIS_E_PERMISSOES
from apps.contas.services import (
    alterar_status_usuario,
    atualizar_permissoes_perfil,
    atualizar_usuario,
    criar_usuario,
    redefinir_senha_usuario,
)

router = Router(tags=["Administração"], auth=django_auth)


class UnidadeSaida(Schema):
    id: int
    codigo: str
    nome: str
    tipo: str
    tipo_descricao: str
    ativa: bool
    usuarios_vinculados: int
    usuarios_ativos: int


class UnidadeCriarEntrada(Schema):
    codigo: str = Field(min_length=2, max_length=50, pattern=r"^[a-z0-9-]+$")
    nome: str = Field(min_length=2, max_length=120)
    tipo: str


class UnidadeAtualizarEntrada(UnidadeCriarEntrada):
    pass


class UsuarioAdministrativoSaida(Schema):
    id: int
    usuario: str
    nome: str
    email: str
    ativo: bool
    perfil: str
    unidade: UnidadeSaida
    deve_trocar_senha: bool


class UsuarioCriarEntrada(Schema):
    usuario: str = Field(min_length=3, max_length=150)
    nome: str = Field(min_length=2, max_length=150)
    email: str = Field(default="", max_length=254)
    senha_temporaria: str = Field(min_length=8, max_length=128)
    perfil: str
    unidade_id: int


class UsuarioAtualizarEntrada(Schema):
    nome: str = Field(min_length=2, max_length=150)
    email: str = Field(default="", max_length=254)
    perfil: str
    unidade_id: int


class RedefinirSenhaEntrada(Schema):
    senha_temporaria: str = Field(min_length=8, max_length=128)


class MensagemSaida(Schema):
    mensagem: str


class PerfilPermissoesEntrada(Schema):
    permissoes: list[str]


class PerfilPermissoesSaida(Schema):
    nome: str
    permissoes: list[str]


def _validar_acesso(request) -> None:
    exigir_permissao(request, GERENCIAR_ACESSOS)


def _erro_validacao(exc: ValidationError) -> HttpError:
    mensagem = "; ".join(exc.messages)
    return HttpError(400, mensagem)


def _serializar_unidade(unidade: Unidade) -> UnidadeSaida:
    usuarios_vinculados = getattr(unidade, "usuarios_vinculados", None)
    usuarios_ativos = getattr(unidade, "usuarios_ativos", None)
    return UnidadeSaida(
        id=unidade.pk,
        codigo=unidade.codigo,
        nome=unidade.nome,
        tipo=unidade.tipo,
        tipo_descricao=unidade.get_tipo_display(),
        ativa=unidade.ativa,
        usuarios_vinculados=(
            usuarios_vinculados
            if usuarios_vinculados is not None
            else unidade.usuarios.count()
        ),
        usuarios_ativos=(
            usuarios_ativos
            if usuarios_ativos is not None
            else unidade.usuarios.filter(is_active=True).count()
        ),
    )


def _serializar_usuario(usuario: Usuario) -> UsuarioAdministrativoSaida:
    return UsuarioAdministrativoSaida(
        id=usuario.pk,
        usuario=usuario.username,
        nome=usuario.get_full_name() or usuario.username,
        email=usuario.email,
        ativo=usuario.is_active,
        perfil=usuario.groups.order_by("name").values_list("name", flat=True).first()
        or "",
        unidade=_serializar_unidade(usuario.unidade),
        deve_trocar_senha=usuario.deve_trocar_senha,
    )


@router.get("/unidades", response=list[UnidadeSaida])
def listar_unidades(request):
    _validar_acesso(request)
    unidades = Unidade.objects.annotate(
        usuarios_vinculados=Count("usuarios", distinct=True),
        usuarios_ativos=Count(
            "usuarios",
            filter=Q(usuarios__is_active=True),
            distinct=True,
        ),
    )
    return [_serializar_unidade(unidade) for unidade in unidades]


@router.post("/unidades", response={201: UnidadeSaida})
def cadastrar_unidade(request, dados: UnidadeCriarEntrada):
    _validar_acesso(request)
    if dados.tipo not in Unidade.Tipo.values:
        raise HttpError(400, "O tipo de unidade informado não é válido.")
    try:
        with transaction.atomic():
            unidade = Unidade.objects.create(
                codigo=dados.codigo.strip(),
                nome=dados.nome.strip(),
                tipo=dados.tipo,
            )
    except IntegrityError as exc:
        raise HttpError(
            400,
            "Já existe uma unidade com esse código ou nome.",
        ) from exc
    return 201, _serializar_unidade(unidade)


@router.patch("/unidades/{unidade_id}", response=UnidadeSaida)
def editar_unidade(request, unidade_id: int, dados: UnidadeAtualizarEntrada):
    _validar_acesso(request)
    unidade = get_object_or_404(Unidade, pk=unidade_id)
    if dados.tipo not in Unidade.Tipo.values:
        raise HttpError(400, "O tipo de unidade informado não é válido.")
    unidade.codigo = dados.codigo.strip()
    unidade.nome = dados.nome.strip()
    unidade.tipo = dados.tipo
    try:
        with transaction.atomic():
            unidade.full_clean()
            unidade.save(update_fields=("codigo", "nome", "tipo", "atualizado_em"))
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    except IntegrityError as exc:
        raise HttpError(
            400,
            "Já existe uma unidade com esse código ou nome.",
        ) from exc
    return _serializar_unidade(unidade)


@router.post("/unidades/{unidade_id}/ativar", response=UnidadeSaida)
def ativar_unidade(request, unidade_id: int):
    _validar_acesso(request)
    unidade = get_object_or_404(Unidade, pk=unidade_id)
    unidade.ativa = True
    unidade.save(update_fields=("ativa", "atualizado_em"))
    return _serializar_unidade(unidade)


@router.post("/unidades/{unidade_id}/desativar", response=UnidadeSaida)
def desativar_unidade(request, unidade_id: int):
    _validar_acesso(request)
    unidade = get_object_or_404(Unidade, pk=unidade_id)
    if unidade.usuarios.filter(is_active=True).exists():
        raise HttpError(
            400,
            "Transfira ou desative os usuários ativos antes de desativar a unidade.",
        )
    unidade.ativa = False
    unidade.save(update_fields=("ativa", "atualizado_em"))
    return _serializar_unidade(unidade)


@router.get("/usuarios", response=list[UsuarioAdministrativoSaida])
def listar_usuarios(
    request,
    busca: str = "",
    ativo: bool | None = None,
    perfil: str = "",
    unidade_id: int | None = None,
):
    _validar_acesso(request)
    usuarios = Usuario.objects.select_related("unidade").prefetch_related("groups")
    if busca.strip():
        termo = busca.strip()
        usuarios = usuarios.filter(
            Q(username__icontains=termo)
            | Q(first_name__icontains=termo)
            | Q(last_name__icontains=termo)
            | Q(email__icontains=termo)
        )
    if ativo is not None:
        usuarios = usuarios.filter(is_active=ativo)
    if perfil:
        usuarios = usuarios.filter(groups__name=perfil)
    if unidade_id is not None:
        usuarios = usuarios.filter(unidade_id=unidade_id)
    return [_serializar_usuario(usuario) for usuario in usuarios.order_by("username")]


@router.post("/usuarios", response={201: UsuarioAdministrativoSaida})
def cadastrar_usuario(request, dados: UsuarioCriarEntrada):
    _validar_acesso(request)
    try:
        usuario = criar_usuario(
            ator=request.user,
            username=dados.usuario,
            nome=dados.nome,
            email=dados.email,
            senha_temporaria=dados.senha_temporaria,
            perfil=dados.perfil,
            unidade_id=dados.unidade_id,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return 201, _serializar_usuario(usuario)


@router.get("/usuarios/{usuario_id}", response=UsuarioAdministrativoSaida)
def consultar_usuario(request, usuario_id: int):
    _validar_acesso(request)
    usuario = get_object_or_404(
        Usuario.objects.select_related("unidade").prefetch_related("groups"),
        pk=usuario_id,
    )
    return _serializar_usuario(usuario)


@router.patch("/usuarios/{usuario_id}", response=UsuarioAdministrativoSaida)
def editar_usuario(request, usuario_id: int, dados: UsuarioAtualizarEntrada):
    _validar_acesso(request)
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    try:
        usuario = atualizar_usuario(
            ator=request.user,
            usuario=usuario,
            nome=dados.nome,
            email=dados.email,
            perfil=dados.perfil,
            unidade_id=dados.unidade_id,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return _serializar_usuario(usuario)


@router.post("/usuarios/{usuario_id}/ativar", response=UsuarioAdministrativoSaida)
def ativar_usuario(request, usuario_id: int):
    _validar_acesso(request)
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    try:
        usuario = alterar_status_usuario(
            ator=request.user,
            usuario=usuario,
            ativo=True,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return _serializar_usuario(usuario)


@router.post("/usuarios/{usuario_id}/desativar", response=UsuarioAdministrativoSaida)
def desativar_usuario(request, usuario_id: int):
    _validar_acesso(request)
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    try:
        usuario = alterar_status_usuario(
            ator=request.user,
            usuario=usuario,
            ativo=False,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return _serializar_usuario(usuario)


@router.post("/usuarios/{usuario_id}/redefinir-senha", response=MensagemSaida)
def redefinir_senha(request, usuario_id: int, dados: RedefinirSenhaEntrada):
    _validar_acesso(request)
    usuario = get_object_or_404(Usuario, pk=usuario_id)
    try:
        redefinir_senha_usuario(
            ator=request.user,
            usuario=usuario,
            senha_temporaria=dados.senha_temporaria,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return MensagemSaida(mensagem="Senha temporária definida com sucesso.")


@router.get("/perfis", response=list[str])
def listar_perfis(request):
    _validar_acesso(request)
    return list(PERFIS_E_PERMISSOES)


@router.patch(
    "/perfis/{perfil_nome}/permissoes",
    response=PerfilPermissoesSaida,
)
def configurar_perfil(request, perfil_nome: str, dados: PerfilPermissoesEntrada):
    _validar_acesso(request)
    try:
        permissoes = atualizar_permissoes_perfil(
            ator=request.user,
            perfil=perfil_nome,
            permissoes=dados.permissoes,
        )
    except ValidationError as exc:
        raise _erro_validacao(exc) from exc
    return PerfilPermissoesSaida(nome=perfil_nome, permissoes=permissoes)
