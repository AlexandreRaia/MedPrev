from django.contrib.auth.models import Group, Permission
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction

from apps.contas.models import EventoAcesso, EventoAutenticacao, Unidade, Usuario
from apps.contas.permissions import PERFIS_E_PERMISSOES


def registrar_evento_autenticacao(
    tipo: str,
    *,
    usuario: Usuario | None = None,
    identificador: str = "",
) -> EventoAutenticacao:
    return EventoAutenticacao.objects.create(
        tipo=tipo,
        usuario=usuario,
        identificador=identificador[:150],
    )


def _validar_perfil(perfil: str) -> Group:
    if perfil not in PERFIS_E_PERMISSOES:
        raise ValidationError("O perfil informado não é válido.")
    return Group.objects.get(name=perfil)


def _validar_unidade(unidade_id: int) -> Unidade:
    try:
        unidade = Unidade.objects.get(pk=unidade_id)
    except Unidade.DoesNotExist as exc:
        raise ValidationError("A unidade informada não existe.") from exc
    if not unidade.ativa:
        raise ValidationError("Não é possível vincular um usuário a uma unidade inativa.")
    return unidade


def _separar_nome(nome: str) -> tuple[str, str]:
    partes = nome.strip().split(maxsplit=1)
    return partes[0], partes[1] if len(partes) == 2 else ""


def _registrar_evento_acesso(
    *,
    ator: Usuario,
    usuario_alvo: Usuario,
    acao: str,
    detalhes: dict | None = None,
) -> EventoAcesso:
    return EventoAcesso.objects.create(
        ator=ator,
        usuario_alvo=usuario_alvo,
        acao=acao,
        detalhes=detalhes or {},
    )


def _garantir_outro_administrador(usuario: Usuario) -> None:
    if not usuario.groups.filter(name="Administrador").exists():
        return
    existem_outros = (
        Usuario.objects.filter(is_active=True, groups__name="Administrador")
        .exclude(pk=usuario.pk)
        .exists()
    )
    if not existem_outros:
        raise ValidationError("O sistema deve manter ao menos um Administrador ativo.")


def _validar_alvo_tecnico(*, ator: Usuario, usuario: Usuario) -> None:
    if usuario.is_superuser and not ator.is_superuser:
        raise ValidationError("Somente outro superusuário pode alterar uma conta técnica.")


@transaction.atomic
def criar_usuario(
    *,
    ator: Usuario,
    username: str,
    nome: str,
    email: str,
    senha_temporaria: str,
    perfil: str,
    unidade_id: int,
) -> Usuario:
    username = username.strip()
    if Usuario.objects.filter(username__iexact=username).exists():
        raise ValidationError("Já existe um usuário com esse nome de acesso.")

    unidade = _validar_unidade(unidade_id)
    grupo = _validar_perfil(perfil)
    primeiro_nome, sobrenome = _separar_nome(nome)
    usuario = Usuario(
        username=username,
        first_name=primeiro_nome,
        last_name=sobrenome,
        email=email.strip(),
        unidade=unidade,
        deve_trocar_senha=True,
    )
    validate_password(senha_temporaria, user=usuario)
    usuario.set_password(senha_temporaria)
    usuario.full_clean(exclude=("password",))
    usuario.save()
    usuario.groups.set([grupo])
    _registrar_evento_acesso(
        ator=ator,
        usuario_alvo=usuario,
        acao=EventoAcesso.Acao.USUARIO_CRIADO,
        detalhes={"perfil": perfil, "unidade_id": unidade.pk},
    )
    return usuario


@transaction.atomic
def atualizar_usuario(
    *,
    ator: Usuario,
    usuario: Usuario,
    nome: str,
    email: str,
    perfil: str,
    unidade_id: int,
) -> Usuario:
    _validar_alvo_tecnico(ator=ator, usuario=usuario)
    grupo = _validar_perfil(perfil)
    unidade = _validar_unidade(unidade_id)
    perfil_atual = usuario.groups.order_by("name").values_list("name", flat=True).first()
    if perfil_atual == "Administrador" and perfil != "Administrador":
        _garantir_outro_administrador(usuario)

    primeiro_nome, sobrenome = _separar_nome(nome)
    usuario.first_name = primeiro_nome
    usuario.last_name = sobrenome
    usuario.email = email.strip()
    usuario.unidade = unidade
    usuario.full_clean(exclude=("password",))
    usuario.save(
        update_fields=(
            "first_name",
            "last_name",
            "email",
            "unidade",
        )
    )
    usuario.groups.set([grupo])
    _registrar_evento_acesso(
        ator=ator,
        usuario_alvo=usuario,
        acao=EventoAcesso.Acao.USUARIO_ATUALIZADO,
        detalhes={"perfil": perfil, "unidade_id": unidade.pk},
    )
    return usuario


@transaction.atomic
def alterar_status_usuario(
    *,
    ator: Usuario,
    usuario: Usuario,
    ativo: bool,
) -> Usuario:
    _validar_alvo_tecnico(ator=ator, usuario=usuario)
    if ator.pk == usuario.pk and not ativo:
        raise ValidationError("Você não pode desativar o próprio usuário.")
    if not ativo:
        _garantir_outro_administrador(usuario)
    usuario.is_active = ativo
    usuario.save(update_fields=("is_active",))
    _registrar_evento_acesso(
        ator=ator,
        usuario_alvo=usuario,
        acao=(EventoAcesso.Acao.USUARIO_ATIVADO if ativo else EventoAcesso.Acao.USUARIO_DESATIVADO),
    )
    return usuario


@transaction.atomic
def redefinir_senha_usuario(
    *,
    ator: Usuario,
    usuario: Usuario,
    senha_temporaria: str,
) -> Usuario:
    _validar_alvo_tecnico(ator=ator, usuario=usuario)
    validate_password(senha_temporaria, user=usuario)
    usuario.set_password(senha_temporaria)
    usuario.deve_trocar_senha = True
    usuario.save(update_fields=("password", "deve_trocar_senha"))
    _registrar_evento_acesso(
        ator=ator,
        usuario_alvo=usuario,
        acao=EventoAcesso.Acao.SENHA_REDEFINIDA,
    )
    return usuario


@transaction.atomic
def alterar_propria_senha(
    *,
    usuario: Usuario,
    senha_atual: str,
    nova_senha: str,
) -> Usuario:
    if not usuario.check_password(senha_atual):
        raise ValidationError("A senha atual está incorreta.")
    validate_password(nova_senha, user=usuario)
    usuario.set_password(nova_senha)
    usuario.deve_trocar_senha = False
    usuario.save(update_fields=("password", "deve_trocar_senha"))
    _registrar_evento_acesso(
        ator=usuario,
        usuario_alvo=usuario,
        acao=EventoAcesso.Acao.SENHA_ALTERADA,
    )
    return usuario


@transaction.atomic
def atualizar_permissoes_perfil(
    *,
    ator: Usuario,
    perfil: str,
    permissoes: list[str],
) -> list[str]:
    if perfil not in PERFIS_E_PERMISSOES:
        raise ValidationError("O perfil informado não é válido.")

    permissoes_validas = {codename for codename, _ in Usuario._meta.permissions}
    novas_permissoes = set(permissoes)
    desconhecidas = novas_permissoes - permissoes_validas
    if desconhecidas:
        raise ValidationError("A matriz contém uma permissão desconhecida.")
    if perfil == "Administrador" and "gerenciar_acessos" not in novas_permissoes:
        raise ValidationError(
            "O perfil Administrador deve manter a permissão de gerenciar acessos."
        )

    grupo = Group.objects.get(name=perfil)
    anteriores = list(
        grupo.permissions.filter(
            content_type__app_label="contas",
            content_type__model="usuario",
        ).values_list("codename", flat=True)
    )
    permissoes_do_banco = Permission.objects.filter(
        content_type__app_label="contas",
        content_type__model="usuario",
        codename__in=novas_permissoes,
    )
    if permissoes_do_banco.count() != len(novas_permissoes):
        raise ValidationError("Uma ou mais permissões não estão disponíveis.")
    grupo.permissions.set(permissoes_do_banco)
    ordenadas = [
        codename for codename, _ in Usuario._meta.permissions if codename in novas_permissoes
    ]
    _registrar_evento_acesso(
        ator=ator,
        usuario_alvo=ator,
        acao=EventoAcesso.Acao.MATRIZ_ATUALIZADA,
        detalhes={
            "perfil": perfil,
            "permissoes_anteriores": sorted(anteriores),
            "permissoes_novas": ordenadas,
        },
    )
    return ordenadas
