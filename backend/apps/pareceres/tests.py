import datetime
import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import Client, TestCase

from apps.apoio.services import criar_solicitacao
from apps.contas.models import Unidade
from apps.legado.models import Pericia, ProtocoloCid, Servidor
from apps.pareceres.models import EventoParecer
from apps.pareceres.services import criar_parecer


class ApiDePareceresTests(TestCase):
    """
    Servidor é managed=False e não existe no banco de teste por migration; a
    estrutura é criada manualmente fora da transação de teste, seguindo o
    mesmo padrão usado em apps.legado.tests.
    """

    @classmethod
    def setUpClass(cls) -> None:
        with connection.schema_editor() as editor:
            editor.create_model(Servidor)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(Servidor)

    def setUp(self) -> None:
        Servidor.objects.create(
            cd_servidor=1001,
            nm_servidor="Servidor Teste",
            cd_funcao=1,
            cd_vinculo=1,
            cd_secretaria=1,
            cd_departamento=1,
            dt_admissao="2020-01-01",
            cd_situacao=1,
        )

        usuario_model = get_user_model()
        unidade = Unidade.objects.get(codigo="medicina-do-trabalho")

        self.medico = usuario_model.objects.create_user(
            username="medico.um", password="Senha-ficticia-123", unidade=unidade
        )
        self.medico.groups.add(Group.objects.get(name="Médico"))

        self.outro_medico = usuario_model.objects.create_user(
            username="medico.dois", password="Senha-ficticia-123", unidade=unidade
        )
        self.outro_medico.groups.add(Group.objects.get(name="Médico"))

        self.enfermagem = usuario_model.objects.create_user(
            username="enfermagem.um", password="Senha-ficticia-123", unidade=unidade
        )
        self.enfermagem.groups.add(Group.objects.get(name="Enfermagem"))

        self.cliente_medico = Client()
        self.cliente_medico.force_login(self.medico)
        self.cliente_outro_medico = Client()
        self.cliente_outro_medico.force_login(self.outro_medico)
        self.cliente_enfermagem = Client()
        self.cliente_enfermagem.force_login(self.enfermagem)

    def _payload_criacao(self, **extra) -> dict:
        payload = {
            "servidor_sismed_id": 1001,
            "texto": "Paciente apresenta melhora clínica.",
            "conclusao": "acompanhamento",
        }
        payload.update(extra)
        return payload

    def _post(self, cliente: Client, caminho: str, dados: dict):
        return cliente.post(caminho, data=json.dumps(dados), content_type="application/json")

    def _patch(self, cliente: Client, caminho: str, dados: dict):
        return cliente.patch(caminho, data=json.dumps(dados), content_type="application/json")

    def test_recusa_usuario_nao_autenticado(self) -> None:
        response = Client().get("/api/v1/pareceres?servidor_sismed_id=1001")

        self.assertEqual(response.status_code, 401)

    def test_recusa_criacao_sem_permissao_de_alterar(self) -> None:
        response = self._post(self.cliente_enfermagem, "/api/v1/pareceres", self._payload_criacao())

        self.assertEqual(response.status_code, 403)

    def test_recusa_listagem_sem_permissao_de_consulta(self) -> None:
        sem_permissao = get_user_model().objects.create_user(
            username="sem.permissao", password="Senha-ficticia-123"
        )
        cliente = Client()
        cliente.force_login(sem_permissao)

        response = cliente.get("/api/v1/pareceres?servidor_sismed_id=1001")

        self.assertEqual(response.status_code, 403)

    def test_recusa_servidor_inexistente(self) -> None:
        response = self._post(
            self.cliente_medico,
            "/api/v1/pareceres",
            self._payload_criacao(servidor_sismed_id=9999),
        )

        self.assertEqual(response.status_code, 400)

    def test_cria_parecer_em_rascunho_por_padrao(self) -> None:
        response = self._post(self.cliente_medico, "/api/v1/pareceres", self._payload_criacao())

        self.assertEqual(response.status_code, 201)
        dados = response.json()
        self.assertEqual(dados["estado"], "rascunho")
        self.assertEqual(dados["autor"], self.medico.get_username())
        self.assertIsNone(dados["concluido_em"])
        self.assertTrue(
            EventoParecer.objects.filter(
                parecer_id=dados["id"], acao=EventoParecer.Acao.CRIADO
            ).exists()
        )

    def test_cria_parecer_ja_concluido_quando_solicitado(self) -> None:
        response = self._post(
            self.cliente_medico,
            "/api/v1/pareceres",
            self._payload_criacao(concluir=True),
        )

        self.assertEqual(response.status_code, 201)
        dados = response.json()
        self.assertEqual(dados["estado"], "concluido")
        self.assertIsNotNone(dados["concluido_em"])

    def test_edita_parecer_em_rascunho(self) -> None:
        criado = self._post(
            self.cliente_medico, "/api/v1/pareceres", self._payload_criacao()
        ).json()

        response = self._patch(
            self.cliente_medico,
            f"/api/v1/pareceres/{criado['id']}",
            {
                "texto": "Texto revisado.",
                "conclusao": "afastamento",
                "prioritario": True,
                "data_reavaliacao": "2026-01-10",
            },
        )

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(dados["texto"], "Texto revisado.")
        self.assertEqual(dados["conclusao"], "afastamento")
        self.assertTrue(dados["prioritario"])
        self.assertTrue(
            EventoParecer.objects.filter(
                parecer_id=criado["id"], acao=EventoParecer.Acao.ATUALIZADO
            ).exists()
        )

    def test_recusa_edicao_por_outro_autor(self) -> None:
        criado = self._post(
            self.cliente_medico, "/api/v1/pareceres", self._payload_criacao()
        ).json()

        response = self._patch(
            self.cliente_outro_medico,
            f"/api/v1/pareceres/{criado['id']}",
            {"texto": "Tentando editar.", "conclusao": "apto"},
        )

        self.assertEqual(response.status_code, 400)

    def test_recusa_edicao_de_parecer_concluido(self) -> None:
        criado = self._post(
            self.cliente_medico,
            "/api/v1/pareceres",
            self._payload_criacao(concluir=True),
        ).json()

        response = self._patch(
            self.cliente_medico,
            f"/api/v1/pareceres/{criado['id']}",
            {"texto": "Tentando editar.", "conclusao": "apto"},
        )

        self.assertEqual(response.status_code, 400)

    def test_conclui_parecer_em_rascunho(self) -> None:
        criado = self._post(
            self.cliente_medico, "/api/v1/pareceres", self._payload_criacao()
        ).json()

        response = self.cliente_medico.post(f"/api/v1/pareceres/{criado['id']}/concluir")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(dados["estado"], "concluido")
        self.assertTrue(
            EventoParecer.objects.filter(
                parecer_id=criado["id"], acao=EventoParecer.Acao.CONCLUIDO
            ).exists()
        )

    def test_recusa_concluir_duas_vezes(self) -> None:
        criado = self._post(
            self.cliente_medico, "/api/v1/pareceres", self._payload_criacao()
        ).json()
        self.cliente_medico.post(f"/api/v1/pareceres/{criado['id']}/concluir")

        response = self.cliente_medico.post(f"/api/v1/pareceres/{criado['id']}/concluir")

        self.assertEqual(response.status_code, 400)

    def test_lista_pareceres_do_servidor(self) -> None:
        self._post(self.cliente_medico, "/api/v1/pareceres", self._payload_criacao())

        response = self.cliente_medico.get("/api/v1/pareceres?servidor_sismed_id=1001")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)


class ApiDeIndicadoresTests(TestCase):
    """
    Servidor, Pericia e ProtocoloCid são managed=False; a estrutura é criada
    manualmente fora da transação de teste, seguindo o mesmo padrão usado em
    apps.legado.tests.
    """

    @classmethod
    def setUpClass(cls) -> None:
        with connection.schema_editor() as editor:
            editor.create_model(Servidor)
            editor.create_model(Pericia)
            editor.create_model(ProtocoloCid)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(ProtocoloCid)
            editor.delete_model(Pericia)
            editor.delete_model(Servidor)

    def setUp(self) -> None:
        hoje = datetime.date.today()

        Servidor.objects.create(
            cd_servidor=1001,
            nm_servidor="Servidor Teste",
            cd_funcao=1,
            cd_vinculo=1,
            cd_secretaria=1,
            cd_departamento=1,
            dt_admissao="2020-01-01",
            cd_situacao=1,
        )

        # Duas perícias dentro da janela de 60 dias, com CIDs diferentes.
        Pericia.objects.create(
            cd_pericia=1,
            cd_protocolo=1,
            dt_pericia=hoje - datetime.timedelta(days=10),
            ic_atestado="t",
        )
        ProtocoloCid.objects.create(cd_protocolocid=1, cd_protocolo=1, cd_cid="M54.5")

        Pericia.objects.create(
            cd_pericia=2,
            cd_protocolo=2,
            dt_pericia=hoje - datetime.timedelta(days=20),
        )
        ProtocoloCid.objects.create(cd_protocolocid=2, cd_protocolo=2, cd_cid="Z00.0")

        # Uma perícia fora da janela de 60 dias: não deve contar em nada.
        Pericia.objects.create(
            cd_pericia=3,
            cd_protocolo=3,
            dt_pericia=hoje - datetime.timedelta(days=90),
            ic_atestado="t",
        )
        ProtocoloCid.objects.create(cd_protocolocid=3, cd_protocolo=3, cd_cid="J06.9")

        usuario_model = get_user_model()
        unidade = Unidade.objects.get(codigo="administracao")

        self.gestor = usuario_model.objects.create_user(
            username="gestor.um", password="Senha-ficticia-123", unidade=unidade
        )
        self.gestor.groups.add(Group.objects.get(name="Gestor da Administração"))
        self.cliente_gestor = Client()
        self.cliente_gestor.force_login(self.gestor)

        self.medico = usuario_model.objects.create_user(
            username="medico.indicadores", password="Senha-ficticia-123", unidade=unidade
        )
        self.medico.groups.add(Group.objects.get(name="Médico"))
        self.cliente_medico = Client()
        self.cliente_medico.force_login(self.medico)

        criar_parecer(
            ator=self.medico,
            servidor_sismed_id=1001,
            protocolo_sismed_id=None,
            texto="Paciente em observação.",
            conclusao="acompanhamento",
            prioritario=False,
            data_reavaliacao=None,
            concluir=False,
        )

    def test_recusa_usuario_nao_autenticado(self) -> None:
        response = Client().get("/api/v1/indicadores")

        self.assertEqual(response.status_code, 401)

    def test_todo_usuario_autenticado_ve_os_indicadores(self) -> None:
        """
        Os números são agregados e não expõem nenhum servidor individualmente,
        então a Visão Geral não depende mais de uma permissão gerencial.
        """
        response = self.cliente_medico.get("/api/v1/indicadores")

        self.assertEqual(response.status_code, 200)

    def test_retorna_indicadores_calculados_a_partir_de_dado_real(self) -> None:
        response = self.cliente_gestor.get("/api/v1/indicadores")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(dados["servidores_acompanhados"], 1)
        self.assertEqual(dados["pericias_60_dias"], 2)
        self.assertEqual(dados["pareceres_em_rascunho"], 1)
        self.assertEqual(dados["pericias_com_atestado_60_dias"], 1)
        codigos = {grupo["codigo"] for grupo in dados["grupos_cid"]}
        self.assertEqual(codigos, {"M54.5", "Z00.0"})

    def test_usuario_de_outra_unidade_ve_pareceres_de_todas_as_unidades(self) -> None:
        """
        A Visão Geral é global para qualquer perfil autenticado: os números
        são agregados e a Consulta já permite localizar qualquer servidor
        independente da unidade, então não faz sentido a Visão Geral mostrar
        só uma fatia.
        """
        outra_unidade = Unidade.objects.get(codigo="medicina-do-trabalho")
        medico_de_outra_unidade = get_user_model().objects.create_user(
            username="medico.outra.unidade",
            password="Senha-ficticia-123",
            unidade=outra_unidade,
        )
        medico_de_outra_unidade.groups.add(Group.objects.get(name="Médico"))
        cliente = Client()
        cliente.force_login(medico_de_outra_unidade)

        response = cliente.get("/api/v1/indicadores")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(dados["servidores_acompanhados"], 1)
        self.assertEqual(dados["pareceres_em_rascunho"], 1)
        self.assertEqual(dados["pericias_60_dias"], 2)

    def test_pendencias_de_apoio_por_perfil(self) -> None:
        seguranca = get_user_model().objects.create_user(
            username="seguranca.indicadores",
            password="Senha-ficticia-123",
            unidade=self.medico.unidade,
        )
        seguranca.groups.add(Group.objects.get(name="Segurança do Trabalho"))
        cliente_seguranca = Client()
        cliente_seguranca.force_login(seguranca)

        criar_solicitacao(
            ator=self.medico,
            servidor_sismed_id=1001,
            protocolo_sismed_id=None,
            especialidade="seguranca_trabalho",
            texto_solicitacao="Avaliar posto de trabalho.",
        )

        resposta_medico = self.cliente_medico.get("/api/v1/indicadores").json()
        resposta_seguranca = cliente_seguranca.get("/api/v1/indicadores").json()
        resposta_gestor = self.cliente_gestor.get("/api/v1/indicadores").json()

        self.assertEqual(resposta_medico["minhas_solicitacoes_pendentes"], 1)
        self.assertEqual(resposta_seguranca["minhas_solicitacoes_pendentes"], 1)
        self.assertIsNone(resposta_gestor["minhas_solicitacoes_pendentes"])
        self.assertEqual(resposta_gestor["solicitacoes_apoio_abertas"], 1)
