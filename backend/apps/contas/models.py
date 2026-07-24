from django.conf import settings
from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models

from apps.contas.permissions import PERMISSOES_DE_NEGOCIO


class Unidade(models.Model):
    class Tipo(models.TextChoices):
        ADMINISTRACAO = "administracao", "Administração"
        SECRETARIA = "secretaria", "Secretaria"
        MEDICINA_TRABALHO = "medicina_trabalho", "Medicina do Trabalho"
        CAIXA_PREVIDENCIA = "caixa_previdencia", "Caixa de Previdência"

    codigo = models.SlugField(max_length=50, unique=True)
    nome = models.CharField(max_length=120, unique=True)
    tipo = models.CharField(max_length=30, choices=Tipo.choices)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("nome",)
        verbose_name = "unidade"
        verbose_name_plural = "unidades"

    def __str__(self) -> str:
        return self.nome


class MedPrevUsuarioManager(UserManager):
    def _unidade_padrao(self) -> Unidade:
        unidade, _ = Unidade.objects.get_or_create(
            codigo="administracao",
            defaults={
                "nome": "Administração",
                "tipo": Unidade.Tipo.ADMINISTRACAO,
            },
        )
        return unidade

    def _create_user(self, username, email, password, **extra_fields):
        extra_fields.setdefault("unidade", self._unidade_padrao())
        return super()._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("unidade", self._unidade_padrao())
        return super().create_superuser(username, email, password, **extra_fields)


class Usuario(AbstractUser):
    """Usuário do MedPrev, vinculado a uma única unidade organizacional."""

    unidade = models.ForeignKey(
        Unidade,
        on_delete=models.PROTECT,
        related_name="usuarios",
    )
    deve_trocar_senha = models.BooleanField(default=False)

    objects = MedPrevUsuarioManager()

    class Meta(AbstractUser.Meta):
        permissions = PERMISSOES_DE_NEGOCIO


class EventoAutenticacao(models.Model):
    class Tipo(models.TextChoices):
        LOGIN_SUCESSO = "login_sucesso", "Login realizado"
        LOGIN_FALHA = "login_falha", "Falha de login"
        LOGOUT = "logout", "Logout realizado"

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_autenticacao",
    )
    identificador = models.CharField(max_length=150, blank=True)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-criado_em", "-id")
        verbose_name = "evento de autenticação"
        verbose_name_plural = "eventos de autenticação"

    def __str__(self) -> str:
        return f"{self.get_tipo_display()} em {self.criado_em:%d/%m/%Y %H:%M:%S}"


class EventoAcesso(models.Model):
    class Acao(models.TextChoices):
        USUARIO_CRIADO = "usuario_criado", "Usuário criado"
        USUARIO_ATUALIZADO = "usuario_atualizado", "Usuário atualizado"
        USUARIO_ATIVADO = "usuario_ativado", "Usuário ativado"
        USUARIO_DESATIVADO = "usuario_desativado", "Usuário desativado"
        SENHA_REDEFINIDA = "senha_redefinida", "Senha redefinida"
        SENHA_ALTERADA = "senha_alterada", "Senha alterada pelo usuário"
        MATRIZ_ATUALIZADA = "matriz_atualizada", "Matriz de acesso atualizada"

    ator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="eventos_acesso_realizados",
    )
    usuario_alvo = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="eventos_acesso_recebidos",
    )
    acao = models.CharField(max_length=30, choices=Acao.choices)
    detalhes = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ("-criado_em", "-id")
        verbose_name = "evento de acesso"
        verbose_name_plural = "eventos de acesso"

    def __str__(self) -> str:
        return f"{self.get_acao_display()}: {self.usuario_alvo}"
