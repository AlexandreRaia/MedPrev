import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import Client, SimpleTestCase, TestCase

from apps.contas.models import EventoAcesso, EventoAutenticacao, Unidade
from apps.contas.permissions import (
    PERFIS_E_PERMISSOES,
    nome_completo_da_permissao,
)


class ConfiguracaoDoUsuarioTests(SimpleTestCase):
    def test_medprev_usa_modelo_de_usuario_proprio(self) -> None:
        usuario_model = get_user_model()

        self.assertEqual(usuario_model._meta.label, "contas.Usuario")


class PerfisIniciaisTests(TestCase):
    def test_migration_configura_os_perfis_esperados(self) -> None:
        self.assertSetEqual(
            set(Group.objects.values_list("name", flat=True)),
            set(PERFIS_E_PERMISSOES),
        )

    def test_cada_perfil_recebe_somente_as_permissoes_previstas(self) -> None:
        for nome, codenames_esperados in PERFIS_E_PERMISSOES.items():
            with self.subTest(perfil=nome):
                grupo = Group.objects.get(name=nome)
                codenames_atuais = set(
                    grupo.permissions.filter(
                        content_type__app_label="contas",
                    ).values_list("codename", flat=True)
                )
                self.assertSetEqual(codenames_atuais, set(codenames_esperados))


class ApiDeAutenticacaoTests(TestCase):
    def setUp(self) -> None:
        usuario_model = get_user_model()
        self.usuario = usuario_model.objects.create_user(
            username="medico.teste",
            password="Senha-ficticia-123",
            first_name="Médico",
            last_name="Teste",
            email="medico@example.test",
        )
        self.cliente = Client(enforce_csrf_checks=True)
        self.csrf_token = self._obter_csrf()

    def _obter_csrf(self) -> str:
        response = self.cliente.get("/api/v1/auth/csrf")
        self.assertEqual(response.status_code, 200)
        self.assertIn("csrftoken", response.cookies)
        return response.json()["csrf_token"]

    def _login(
        self,
        *,
        usuario: str = "medico.teste",
        senha: str = "Senha-ficticia-123",
    ):
        return self.cliente.post(
            "/api/v1/auth/login",
            data=json.dumps({"usuario": usuario, "senha": senha}),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token,
        )

    def test_login_exige_csrf(self) -> None:
        response = self.cliente.post(
            "/api/v1/auth/login",
            data=json.dumps(
                {
                    "usuario": "medico.teste",
                    "senha": "Senha-ficticia-123",
                }
            ),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 403)

    def test_credenciais_invalidas_retornam_401_e_sao_auditadas(self) -> None:
        response = self._login(senha="senha-incorreta")

        self.assertEqual(response.status_code, 401)
        evento = EventoAutenticacao.objects.get()
        self.assertEqual(evento.tipo, EventoAutenticacao.Tipo.LOGIN_FALHA)
        self.assertEqual(evento.identificador, "medico.teste")
        self.assertIsNone(evento.usuario)

    def test_login_e_consulta_da_sessao(self) -> None:
        self.usuario.groups.add(Group.objects.get(name="Médico"))

        login_response = self._login()
        me_response = self.cliente.get("/api/v1/auth/me")

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(me_response.status_code, 200)
        self.assertEqual(me_response.json()["usuario"], "medico.teste")
        self.assertEqual(me_response.json()["nome"], "Médico Teste")
        self.assertEqual(me_response.json()["grupos"], ["Médico"])
        self.assertEqual(me_response.json()["unidade"]["codigo"], "administracao")
        self.assertSetEqual(
            set(me_response.json()["permissoes"]),
            set(PERFIS_E_PERMISSOES["Médico"]),
        )
        self.assertTrue(
            EventoAutenticacao.objects.filter(
                tipo=EventoAutenticacao.Tipo.LOGIN_SUCESSO,
                usuario=self.usuario,
            ).exists()
        )

    def test_sessao_atual_recusa_usuario_nao_autenticado(self) -> None:
        response = self.cliente.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 401)

    def test_matriz_recusa_usuario_sem_permissao(self) -> None:
        self.usuario.groups.add(Group.objects.get(name="Operador Administrativo"))
        self.assertEqual(self._login().status_code, 200)

        response = self.cliente.get("/api/v1/auth/matriz")

        self.assertEqual(response.status_code, 403)

    def test_matriz_permite_administrador(self) -> None:
        self.usuario.groups.add(Group.objects.get(name="Administrador"))
        self.assertTrue(self.usuario.has_perm(nome_completo_da_permissao("gerenciar_acessos")))
        self.assertEqual(self._login().status_code, 200)

        response = self.cliente.get("/api/v1/auth/matriz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {perfil["nome"] for perfil in response.json()},
            set(PERFIS_E_PERMISSOES),
        )

    def test_logout_encerra_sessao_e_registra_auditoria(self) -> None:
        self.assertEqual(self._login().status_code, 200)
        csrf_token_renovado = self.cliente.cookies["csrftoken"].value

        logout_response = self.cliente.post(
            "/api/v1/auth/logout",
            HTTP_X_CSRFTOKEN=csrf_token_renovado,
        )
        me_response = self.cliente.get("/api/v1/auth/me")

        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(me_response.status_code, 401)
        self.assertTrue(
            EventoAutenticacao.objects.filter(
                tipo=EventoAutenticacao.Tipo.LOGOUT,
                usuario=self.usuario,
            ).exists()
        )

    def test_usuario_altera_senha_temporaria_no_primeiro_acesso(self) -> None:
        self.usuario.deve_trocar_senha = True
        self.usuario.save(update_fields=("deve_trocar_senha",))
        self.assertEqual(self._login().status_code, 200)
        csrf_token_renovado = self.cliente.cookies["csrftoken"].value

        response = self.cliente.post(
            "/api/v1/auth/alterar-senha",
            data=json.dumps(
                {
                    "senha_atual": "Senha-ficticia-123",
                    "nova_senha": "Nova-senha-ficticia-456",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=csrf_token_renovado,
        )
        sessao_response = self.cliente.get("/api/v1/auth/me")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(sessao_response.status_code, 200)
        self.assertEqual(sessao_response.json()["usuario"], "medico.teste")
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.deve_trocar_senha)
        self.assertTrue(self.usuario.check_password("Nova-senha-ficticia-456"))
        self.assertTrue(
            EventoAcesso.objects.filter(
                usuario_alvo=self.usuario,
                acao=EventoAcesso.Acao.SENHA_ALTERADA,
            ).exists()
        )


class ApiAdministrativaTests(TestCase):
    def setUp(self) -> None:
        usuario_model = get_user_model()
        self.unidade = Unidade.objects.get(codigo="administracao")
        self.admin = usuario_model.objects.create_user(
            username="administrador.teste",
            password="Senha-ficticia-123",
            first_name="Administrador",
            unidade=self.unidade,
        )
        self.admin.groups.add(Group.objects.get(name="Administrador"))
        self.cliente = Client(enforce_csrf_checks=True)
        self.csrf_token = self.cliente.get("/api/v1/auth/csrf").json()["csrf_token"]
        response = self.cliente.post(
            "/api/v1/auth/login",
            data=json.dumps(
                {
                    "usuario": "administrador.teste",
                    "senha": "Senha-ficticia-123",
                }
            ),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token,
        )
        self.assertEqual(response.status_code, 200)
        self.csrf_token = self.cliente.cookies["csrftoken"].value

    def _post(self, caminho: str, dados: dict):
        return self.cliente.post(
            caminho,
            data=json.dumps(dados),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token,
        )

    def _patch(self, caminho: str, dados: dict):
        return self.cliente.patch(
            caminho,
            data=json.dumps(dados),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.csrf_token,
        )

    def test_cria_usuario_com_uma_unidade_um_perfil_e_auditoria(self) -> None:
        response = self._post(
            "/api/v1/administracao/usuarios",
            {
                "usuario": "medico.teste2",
                "nome": "Médico Teste",
                "email": "medico2@example.test",
                "senha_temporaria": "Senha-temporaria-456",
                "perfil": "Médico",
                "unidade_id": self.unidade.pk,
            },
        )

        self.assertEqual(response.status_code, 201)
        usuario = get_user_model().objects.get(username="medico.teste2")
        self.assertEqual(usuario.unidade, self.unidade)
        self.assertEqual(list(usuario.groups.values_list("name", flat=True)), ["Médico"])
        self.assertTrue(usuario.deve_trocar_senha)
        self.assertTrue(
            EventoAcesso.objects.filter(
                usuario_alvo=usuario,
                ator=self.admin,
                acao=EventoAcesso.Acao.USUARIO_CRIADO,
            ).exists()
        )

    def test_nao_permite_desativar_o_proprio_usuario(self) -> None:
        response = self._post(
            f"/api/v1/administracao/usuarios/{self.admin.pk}/desativar",
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_usuario_sem_permissao_nao_acessa_administracao(self) -> None:
        self.cliente.logout()
        usuario = get_user_model().objects.create_user(
            username="operador.teste",
            password="Senha-ficticia-123",
            unidade=self.unidade,
        )
        usuario.groups.add(Group.objects.get(name="Operador Administrativo"))
        self.cliente.force_login(usuario)

        response = self.cliente.get("/api/v1/administracao/usuarios")

        self.assertEqual(response.status_code, 403)

    def test_edita_unidade(self) -> None:
        unidade = Unidade.objects.create(
            codigo="secretaria-teste",
            nome="Secretaria Teste",
            tipo=Unidade.Tipo.SECRETARIA,
        )

        response = self._patch(
            f"/api/v1/administracao/unidades/{unidade.pk}",
            {
                "codigo": "secretaria-educacao",
                "nome": "Secretaria de Educação",
                "tipo": Unidade.Tipo.SECRETARIA,
            },
        )

        self.assertEqual(response.status_code, 200)
        unidade.refresh_from_db()
        self.assertEqual(unidade.codigo, "secretaria-educacao")
        self.assertEqual(unidade.nome, "Secretaria de Educação")

    def test_nao_desativa_unidade_com_usuario_ativo(self) -> None:
        response = self._post(
            f"/api/v1/administracao/unidades/{self.unidade.pk}/desativar",
            {},
        )

        self.assertEqual(response.status_code, 400)
        self.unidade.refresh_from_db()
        self.assertTrue(self.unidade.ativa)

    def test_desativa_e_reativa_unidade_sem_usuarios_ativos(self) -> None:
        unidade = Unidade.objects.create(
            codigo="secretaria-vazia",
            nome="Secretaria Vazia",
            tipo=Unidade.Tipo.SECRETARIA,
        )

        desativar = self._post(
            f"/api/v1/administracao/unidades/{unidade.pk}/desativar",
            {},
        )
        reativar = self._post(
            f"/api/v1/administracao/unidades/{unidade.pk}/ativar",
            {},
        )

        self.assertEqual(desativar.status_code, 200)
        self.assertFalse(desativar.json()["ativa"])
        self.assertEqual(reativar.status_code, 200)
        self.assertTrue(reativar.json()["ativa"])

    def test_lista_quantidade_de_usuarios_da_unidade(self) -> None:
        response = self.cliente.get("/api/v1/administracao/unidades")

        self.assertEqual(response.status_code, 200)
        administracao = next(item for item in response.json() if item["codigo"] == "administracao")
        self.assertEqual(administracao["usuarios_vinculados"], 1)
        self.assertEqual(administracao["usuarios_ativos"], 1)

    def test_configura_permissoes_de_um_perfil_e_audita(self) -> None:
        response = self._patch(
            "/api/v1/administracao/perfis/Enfermagem/permissoes",
            {
                "permissoes": [
                    "consultar_dados",
                    "consultar_conteudo_medico",
                    "visualizar_dados_globais",
                ]
            },
        )

        self.assertEqual(response.status_code, 200)
        grupo = Group.objects.get(name="Enfermagem")
        self.assertSetEqual(
            set(
                grupo.permissions.filter(
                    content_type__app_label="contas",
                ).values_list("codename", flat=True)
            ),
            {
                "consultar_dados",
                "consultar_conteudo_medico",
                "visualizar_dados_globais",
            },
        )
        self.assertTrue(
            EventoAcesso.objects.filter(
                ator=self.admin,
                acao=EventoAcesso.Acao.MATRIZ_ATUALIZADA,
                detalhes__perfil="Enfermagem",
            ).exists()
        )

    def test_administrador_nao_pode_perder_gerenciamento_de_acessos(self) -> None:
        response = self._patch(
            "/api/v1/administracao/perfis/Administrador/permissoes",
            {"permissoes": ["consultar_dados"]},
        )

        self.assertEqual(response.status_code, 400)
        self.assertTrue(
            Group.objects.get(name="Administrador")
            .permissions.filter(
                codename="gerenciar_acessos",
            )
            .exists()
        )
