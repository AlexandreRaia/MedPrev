from django.db import migrations


PERMISSOES_DE_NEGOCIO = (
    ("gerenciar_acessos", "Pode gerenciar usuários, grupos e permissões"),
    ("consultar_dados", "Pode consultar dados cadastrais e administrativos"),
    ("alterar_dados_administrativos", "Pode alterar dados administrativos"),
    ("consultar_conteudo_medico", "Pode consultar conteúdo médico"),
    ("alterar_conteudo_medico", "Pode criar e alterar conteúdo médico"),
    ("visualizar_dados_globais", "Pode visualizar dados de todas as unidades"),
    (
        "solicitar_apoio_especializado",
        "Pode solicitar apoio de especialista (Neuropsicólogo, Assistente "
        "Social, Segurança do Trabalho)",
    ),
    (
        "responder_solicitacao_apoio",
        "Pode responder solicitações de apoio direcionadas à sua especialidade",
    ),
)


def remover_perfil_auditor(apps, schema_editor) -> None:
    del schema_editor
    content_type_model = apps.get_model("contenttypes", "ContentType")
    group_model = apps.get_model("auth", "Group")
    permission_model = apps.get_model("auth", "Permission")

    # Sem perfil sucessor: o Auditor não tinha nenhuma permissão exclusiva que
    # outro perfil de negócio precise herdar (Administrador já enxerga tudo).
    group_model.objects.filter(name="Auditor").delete()

    content_type, _ = content_type_model.objects.get_or_create(
        app_label="contas",
        model="usuario",
    )
    permission_model.objects.filter(
        content_type=content_type,
        codename="visualizar_auditoria",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0006_perfis_multidisciplinares"),
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
        migrations.RunPython(
            remover_perfil_auditor,
            migrations.RunPython.noop,
        ),
    ]
