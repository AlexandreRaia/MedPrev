import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


PERMISSOES_DE_NEGOCIO = (
    ("gerenciar_acessos", "Pode gerenciar usuários, grupos e permissões"),
    ("consultar_dados", "Pode consultar dados cadastrais e administrativos"),
    (
        "alterar_dados_administrativos",
        "Pode alterar dados administrativos",
    ),
    ("consultar_conteudo_medico", "Pode consultar conteúdo médico"),
    ("alterar_conteudo_medico", "Pode criar e alterar conteúdo médico"),
    ("visualizar_auditoria", "Pode visualizar a auditoria"),
)

PERFIS_E_PERMISSOES = {
    "Administrador": tuple(codename for codename, _ in PERMISSOES_DE_NEGOCIO),
    "Médico/Perito": (
        "consultar_dados",
        "consultar_conteudo_medico",
        "alterar_conteudo_medico",
    ),
    "Atendimento": (
        "consultar_dados",
        "alterar_dados_administrativos",
    ),
    "Auditor": (
        "consultar_dados",
        "consultar_conteudo_medico",
        "visualizar_auditoria",
    ),
}


def criar_perfis(apps, schema_editor) -> None:
    del schema_editor
    content_type_model = apps.get_model("contenttypes", "ContentType")
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")

    content_type, _ = content_type_model.objects.get_or_create(
        app_label="contas",
        model="usuario",
    )
    permissions = {}
    for codename, name in PERMISSOES_DE_NEGOCIO:
        permission, _ = permission_model.objects.update_or_create(
            content_type=content_type,
            codename=codename,
            defaults={"name": name},
        )
        permissions[codename] = permission

    for group_name, permission_codenames in PERFIS_E_PERMISSOES.items():
        group, _ = group_model.objects.get_or_create(name=group_name)
        group.permissions.set(
            permissions[codename] for codename in permission_codenames
        )


def remover_perfis(apps, schema_editor) -> None:
    del schema_editor
    group_model = apps.get_model("auth", "Group")
    group_model.objects.filter(name__in=PERFIS_E_PERMISSOES).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0001_initial"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="usuario",
            options={
                "permissions": PERMISSOES_DE_NEGOCIO,
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
        migrations.CreateModel(
            name="EventoAutenticacao",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "identificador",
                    models.CharField(blank=True, max_length=150),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("login_sucesso", "Login realizado"),
                            ("login_falha", "Falha de login"),
                            ("logout", "Logout realizado"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "usuario",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="eventos_autenticacao",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "evento de autenticação",
                "verbose_name_plural": "eventos de autenticação",
                "ordering": ("-criado_em", "-id"),
            },
        ),
        migrations.RunPython(criar_perfis, remover_perfis),
    ]
