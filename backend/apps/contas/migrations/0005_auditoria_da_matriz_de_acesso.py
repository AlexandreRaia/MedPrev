from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("contas", "0004_evento_de_alteracao_de_senha"),
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
                    ("matriz_atualizada", "Matriz de acesso atualizada"),
                ],
                max_length=30,
            ),
        ),
    ]
