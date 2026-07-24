from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0003_unidades_e_gestao_de_acessos"),
    ]

    operations = [
        migrations.AlterField(
            model_name="eventoacesso",
            name="acao",
            field=models.CharField(
                choices=[
                    ("usuario_criado", "Usuário criado"),
                    ("usuario_atualizado", "Usuário atualizado"),
                    ("usuario_ativado", "Usuário ativado"),
                    ("usuario_desativado", "Usuário desativado"),
                    ("senha_redefinida", "Senha redefinida"),
                    ("senha_alterada", "Senha alterada pelo usuário"),
                ],
                max_length=30,
            ),
        ),
    ]
