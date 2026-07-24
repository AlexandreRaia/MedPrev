import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

import apps.contas.models


PERMISSOES_DE_NEGOCIO = (
    ("gerenciar_acessos", "Pode gerenciar usuários, grupos e permissões"),
    ("consultar_dados", "Pode consultar dados cadastrais e administrativos"),
    ("alterar_dados_administrativos", "Pode alterar dados administrativos"),
    ("consultar_conteudo_medico", "Pode consultar conteúdo médico"),
    ("alterar_conteudo_medico", "Pode criar e alterar conteúdo médico"),
    ("visualizar_auditoria", "Pode visualizar a auditoria"),
    ("visualizar_dados_globais", "Pode visualizar dados de todas as unidades"),
    (
        "visualizar_indicadores_gerenciais",
        "Pode visualizar indicadores gerenciais",
    ),
)

PERFIS_E_PERMISSOES = {
    "Administrador": tuple(codename for codename, _ in PERMISSOES_DE_NEGOCIO),
    "Gestor da Administração": (
        "consultar_dados",
        "visualizar_dados_globais",
        "visualizar_indicadores_gerenciais",
    ),
    "Operador Administrativo": (
        "consultar_dados",
        "alterar_dados_administrativos",
    ),
    "Médico do Trabalho": (
        "consultar_dados",
        "consultar_conteudo_medico",
        "alterar_conteudo_medico",
    ),
    "Médico Perito": (
        "consultar_dados",
        "consultar_conteudo_medico",
        "alterar_conteudo_medico",
    ),
    "Auditor": (
        "consultar_dados",
        "visualizar_auditoria",
    ),
}


def configurar_unidades_e_perfis(apps, schema_editor) -> None:
    del schema_editor
    unidade_model = apps.get_model("contas", "Unidade")
    usuario_model = apps.get_model("contas", "Usuario")
    content_type_model = apps.get_model("contenttypes", "ContentType")
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")

    administracao, _ = unidade_model.objects.get_or_create(
        codigo="administracao",
        defaults={"nome": "Administração", "tipo": "administracao"},
    )
    unidade_model.objects.get_or_create(
        codigo="medicina-do-trabalho",
        defaults={
            "nome": "Medicina do Trabalho",
            "tipo": "medicina_trabalho",
        },
    )
    unidade_model.objects.get_or_create(
        codigo="caixa-de-previdencia",
        defaults={
            "nome": "Caixa de Previdência",
            "tipo": "caixa_previdencia",
        },
    )
    usuario_model.objects.filter(unidade__isnull=True).update(unidade=administracao)

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

    grupo_antigo_medico = group_model.objects.filter(name="Médico/Perito").first()
    grupo_antigo_atendimento = group_model.objects.filter(name="Atendimento").first()
    grupo_medico_perito, _ = group_model.objects.get_or_create(name="Médico Perito")
    grupo_operador, _ = group_model.objects.get_or_create(
        name="Operador Administrativo"
    )
    if grupo_antigo_medico:
        for usuario in grupo_antigo_medico.user_set.all():
            usuario.groups.add(grupo_medico_perito)
    if grupo_antigo_atendimento:
        for usuario in grupo_antigo_atendimento.user_set.all():
            usuario.groups.add(grupo_operador)

    for group_name, permission_codenames in PERFIS_E_PERMISSOES.items():
        group, _ = group_model.objects.get_or_create(name=group_name)
        group.permissions.set(
            permissions[codename] for codename in permission_codenames
        )

    group_model.objects.filter(name__in=("Médico/Perito", "Atendimento")).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0002_autenticacao_e_perfis"),
    ]

    operations = [
        migrations.CreateModel(
            name="Unidade",
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
                ("codigo", models.SlugField(max_length=50, unique=True)),
                ("nome", models.CharField(max_length=120, unique=True)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("administracao", "Administração"),
                            ("secretaria", "Secretaria"),
                            ("medicina_trabalho", "Medicina do Trabalho"),
                            ("caixa_previdencia", "Caixa de Previdência"),
                        ],
                        max_length=30,
                    ),
                ),
                ("ativa", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "unidade",
                "verbose_name_plural": "unidades",
                "ordering": ("nome",),
            },
        ),
        migrations.AddField(
            model_name="usuario",
            name="deve_trocar_senha",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="usuario",
            name="unidade",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="usuarios",
                to="contas.unidade",
            ),
        ),
        migrations.RunPython(
            configurar_unidades_e_perfis,
            migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="usuario",
            name="unidade",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="usuarios",
                to="contas.unidade",
            ),
        ),
        migrations.AlterModelManagers(
            name="usuario",
            managers=[
                ("objects", apps.contas.models.MedPrevUsuarioManager()),
            ],
        ),
        migrations.AlterModelOptions(
            name="usuario",
            options={
                "permissions": PERMISSOES_DE_NEGOCIO,
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
        migrations.CreateModel(
            name="EventoAcesso",
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
                    "acao",
                    models.CharField(
                        choices=[
                            ("usuario_criado", "Usuário criado"),
                            ("usuario_atualizado", "Usuário atualizado"),
                            ("usuario_ativado", "Usuário ativado"),
                            ("usuario_desativado", "Usuário desativado"),
                            ("senha_redefinida", "Senha redefinida"),
                        ],
                        max_length=30,
                    ),
                ),
                ("detalhes", models.JSONField(blank=True, default=dict)),
                (
                    "criado_em",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
                (
                    "ator",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="eventos_acesso_realizados",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "usuario_alvo",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="eventos_acesso_recebidos",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "evento de acesso",
                "verbose_name_plural": "eventos de acesso",
                "ordering": ("-criado_em", "-id"),
            },
        ),
    ]
