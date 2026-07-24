from django.contrib.auth import get_user_model
from django.test import SimpleTestCase


class ConfiguracaoDoUsuarioTests(SimpleTestCase):
    def test_medprev_usa_modelo_de_usuario_proprio(self) -> None:
        usuario_model = get_user_model()

        self.assertEqual(usuario_model._meta.label, "contas.Usuario")
