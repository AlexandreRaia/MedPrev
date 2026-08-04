from django.db import migrations


PERMISSOES_DE_NEGOCIO = (
    ("gerenciar_acessos", "Pode gerenciar usuários, grupos e permissões"),
    ("consultar_dados", "Pode consultar dados cadastrais e administrativos"),
    ("alterar_dados_administrativos", "Pode alterar dados administrativos"),
    ("consultar_conteudo_medico", "Pode consultar conteúdo médico"),
    ("alterar_conteudo_medico", "Pode criar e alterar conteúdo médico"),
    ("visualizar_auditoria", "Pode visualizar a auditoria"),
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

PERFIS_E_PERMISSOES = {
    "Administrador": tuple(codename for codename, _ in PERMISSOES_DE_NEGOCIO),
    "Gestor da Administração": (
        "consultar_dados",
        "visualizar_dados_globais",
    ),
    "Operador Administrativo": (
        "consultar_dados",
        "alterar_dados_administrativos",
    ),
    "Médico": (
        "consultar_dados",
        "consultar_conteudo_medico",
        "alterar_conteudo_medico",
        "solicitar_apoio_especializado",
    ),
    "Enfermagem": (
        "consultar_dados",
        "consultar_conteudo_medico",
    ),
    "Neuropsicólogo": ("responder_solicitacao_apoio",),
    "Assistente Social": ("responder_solicitacao_apoio",),
    "Segurança do Trabalho": ("responder_solicitacao_apoio",),
    "Auditor": (
        "consultar_dados",
        "visualizar_auditoria",
    ),
}


def ajustar_perfis_multidisciplinares(apps, schema_editor) -> None:
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

    # "Médico do Trabalho" vira "Médico": mesma linha de Group, preserva os
    # usuários já vinculados. "Médico Perito" tinha exatamente as mesmas
    # permissões (redundante) e é removido; seus usuários migram para "Médico".
    grupo_medico = group_model.objects.filter(name="Médico do Trabalho").first()
    if grupo_medico:
        grupo_medico.name = "Médico"
        grupo_medico.save(update_fields=["name"])
    else:
        grupo_medico, _ = group_model.objects.get_or_create(name="Médico")

    grupo_perito = group_model.objects.filter(name="Médico Perito").first()
    if grupo_perito:
        for usuario in grupo_perito.user_set.all():
            usuario.groups.add(grupo_medico)
        grupo_perito.delete()

    for group_name, permission_codenames in PERFIS_E_PERMISSOES.items():
        group, _ = group_model.objects.get_or_create(name=group_name)
        group.permissions.set(
            permissions[codename] for codename in permission_codenames
        )

    # A Visão Geral deixa de ser exclusiva de quem tem essa permissão (os
    # indicadores são agregados e não expõem nenhum servidor individualmente).
    permission_model.objects.filter(
        content_type=content_type,
        codename="visualizar_indicadores_gerenciais",
    ).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0005_auditoria_da_matriz_de_acesso"),
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
            ajustar_perfis_multidisciplinares,
            migrations.RunPython.noop,
        ),
    ]
