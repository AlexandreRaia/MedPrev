import json

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection
from django.test import Client, TestCase

from apps.apoio.models import EventoSolicitacaoApoio, SolicitacaoApoio
from apps.contas.models import Unidade
from apps.legado.models import Protocolo, Servidor, SituacaoProtocolo
from apps.pareceres.services import concluir_parecer, criar_parecer


class ApiDeApoioTests(TestCase):
    """
    Servidor é managed=False e não existe no banco de teste por migration; a
    estrutura é criada manualmente fora da transação de teste, seguindo o
    mesmo padrão usado em apps.legado.tests e apps.pareceres.tests.
    """

    @classmethod
    def setUpClass(cls) -> None:
        with connection.schema_editor() as editor:
            editor.create_model(Servidor)
            editor.create_model(SituacaoProtocolo)
            editor.create_model(Protocolo)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(Protocolo)
            editor.delete_model(SituacaoProtocolo)
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
            username="medico.apoio", password="Senha-ficticia-123", unidade=unidade
        )
        self.medico.groups.add(Group.objects.get(name="Médico"))

        self.enfermagem = usuario_model.objects.create_user(
            username="enfermagem.apoio", password="Senha-ficticia-123", unidade=unidade
        )
        self.enfermagem.groups.add(Group.objects.get(name="Enfermagem"))

        self.seguranca = usuario_model.objects.create_user(
            username="seguranca.apoio", password="Senha-ficticia-123", unidade=unidade
        )
        self.seguranca.groups.add(Group.objects.get(name="Segurança do Trabalho"))

        self.assistente_social = usuario_model.objects.create_user(
            username="social.apoio", password="Senha-ficticia-123", unidade=unidade
        )
        self.assistente_social.groups.add(Group.objects.get(name="Assistente Social"))

        self.cliente_medico = Client()
        self.cliente_medico.force_login(self.medico)
        self.cliente_enfermagem = Client()
        self.cliente_enfermagem.force_login(self.enfermagem)
        self.cliente_seguranca = Client()
        self.cliente_seguranca.force_login(self.seguranca)
        self.cliente_social = Client()
        self.cliente_social.force_login(self.assistente_social)

    def _payload_criacao(self, **extra) -> dict:
        payload = {
            "servidor_sismed_id": 1001,
            "especialidade": "seguranca_trabalho",
            "texto_solicitacao": "Avaliar risco ergonômico do posto de trabalho.",
        }
        payload.update(extra)
        return payload

    def _post(self, cliente: Client, caminho: str, dados: dict):
        return cliente.post(caminho, data=json.dumps(dados), content_type="application/json")

    def test_recusa_usuario_nao_autenticado(self) -> None:
        response = Client().get("/api/v1/apoio?servidor_sismed_id=1001")

        self.assertEqual(response.status_code, 401)

    def test_recusa_criacao_sem_permissao_de_solicitar(self) -> None:
        response = self._post(self.cliente_enfermagem, "/api/v1/apoio", self._payload_criacao())

        self.assertEqual(response.status_code, 403)

    def test_recusa_servidor_inexistente(self) -> None:
        response = self._post(
            self.cliente_medico,
            "/api/v1/apoio",
            self._payload_criacao(servidor_sismed_id=9999),
        )

        self.assertEqual(response.status_code, 400)

    def test_cria_solicitacao_em_aberto(self) -> None:
        response = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao())

        self.assertEqual(response.status_code, 201)
        dados = response.json()
        self.assertEqual(dados["estado"], "aberta")
        self.assertEqual(dados["especialidade"], "seguranca_trabalho")
        self.assertIsNone(dados["respondente"])
        self.assertTrue(
            EventoSolicitacaoApoio.objects.filter(
                solicitacao_id=dados["id"], acao=EventoSolicitacaoApoio.Acao.CRIADA
            ).exists()
        )

    def test_recusa_listagem_do_servidor_sem_permissao_medica(self) -> None:
        response = self.cliente_seguranca.get("/api/v1/apoio?servidor_sismed_id=1001")

        self.assertEqual(response.status_code, 403)

    def test_lista_solicitacoes_do_servidor_para_quem_ve_conteudo_medico(self) -> None:
        self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao())

        response = self.cliente_enfermagem.get("/api/v1/apoio?servidor_sismed_id=1001")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    def test_recusa_resposta_sem_permissao(self) -> None:
        criada = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao()).json()

        response = self._post(
            self.cliente_medico,
            f"/api/v1/apoio/{criada['id']}/responder",
            {"texto_resposta": "Análise concluída."},
        )

        self.assertEqual(response.status_code, 403)

    def test_recusa_resposta_de_especialidade_errada(self) -> None:
        criada = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao()).json()

        response = self._post(
            self.cliente_social,
            f"/api/v1/apoio/{criada['id']}/responder",
            {"texto_resposta": "Análise concluída."},
        )

        self.assertEqual(response.status_code, 400)

    def test_responde_solicitacao_da_propria_especialidade(self) -> None:
        criada = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao()).json()

        response = self._post(
            self.cliente_seguranca,
            f"/api/v1/apoio/{criada['id']}/responder",
            {"texto_resposta": "Posto avaliado, sem risco relevante."},
        )

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(dados["estado"], "respondida")
        self.assertEqual(dados["respondente"], self.seguranca.get_username())
        self.assertTrue(
            EventoSolicitacaoApoio.objects.filter(
                solicitacao_id=criada["id"], acao=EventoSolicitacaoApoio.Acao.RESPONDIDA
            ).exists()
        )

    def test_recusa_responder_solicitacao_ja_respondida(self) -> None:
        criada = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao()).json()
        self._post(
            self.cliente_seguranca,
            f"/api/v1/apoio/{criada['id']}/responder",
            {"texto_resposta": "Primeira resposta."},
        )

        response = self._post(
            self.cliente_seguranca,
            f"/api/v1/apoio/{criada['id']}/responder",
            {"texto_resposta": "Segunda tentativa."},
        )

        self.assertEqual(response.status_code, 400)

    def test_lista_minhas_solicitacoes_filtra_pela_especialidade(self) -> None:
        self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao())
        self._post(
            self.cliente_medico,
            "/api/v1/apoio",
            self._payload_criacao(especialidade="assistencia_social"),
        )

        resposta_seguranca = self.cliente_seguranca.get("/api/v1/apoio/minhas")
        resposta_social = self.cliente_social.get("/api/v1/apoio/minhas")

        self.assertEqual(len(resposta_seguranca.json()), 1)
        self.assertEqual(resposta_seguranca.json()[0]["especialidade"], "seguranca_trabalho")
        self.assertEqual(resposta_seguranca.json()[0]["servidor_nome"], "Servidor Teste")
        self.assertEqual(len(resposta_social.json()), 1)
        self.assertEqual(resposta_social.json()[0]["especialidade"], "assistencia_social")

    def test_minhas_solicitacoes_nao_mostra_as_ja_respondidas(self) -> None:
        criada = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao()).json()
        self._post(
            self.cliente_seguranca,
            f"/api/v1/apoio/{criada['id']}/responder",
            {"texto_resposta": "Concluído."},
        )

        response = self.cliente_seguranca.get("/api/v1/apoio/minhas")

        self.assertEqual(response.json(), [])

    def test_solicitacao_e_escopada_pela_unidade_do_solicitante(self) -> None:
        response = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao())

        solicitacao = SolicitacaoApoio.objects.get(pk=response.json()["id"])
        self.assertEqual(solicitacao.unidade, self.medico.unidade)

    def test_recusa_atendimentos_sem_permissao(self) -> None:
        response = self.cliente_enfermagem.get("/api/v1/apoio/atendimentos")

        self.assertEqual(response.status_code, 403)

    def test_atendimentos_mostra_solicitacao_aberta_sem_parecer(self) -> None:
        self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao())

        response = self.cliente_medico.get("/api/v1/apoio/atendimentos")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["servidor_sismed_id"], 1001)
        self.assertEqual(dados[0]["servidor_nome"], "Servidor Teste")
        self.assertFalse(dados[0]["parecer_em_aberto"])
        self.assertIsNone(dados[0]["parecer_autor"])
        self.assertIsNone(dados[0]["situacao_protocolo"])
        self.assertEqual(
            dados[0]["apoios"],
            [
                {
                    "especialidade": "seguranca_trabalho",
                    "especialidade_descricao": "Segurança do Trabalho",
                    "estado": "aberta",
                    "estado_descricao": "Aguardando resposta",
                }
            ],
        )

    def test_atendimentos_mostra_situacao_do_protocolo_mais_recente(self) -> None:
        situacao = SituacaoProtocolo.objects.create(
            cd_situacaoprotocolo=1,
            ds_situacaoprotocolo="Em analise",
            st_ativo=True,
        )
        Protocolo.objects.create(
            cd_protocolo=1,
            dt_protocolo="2026-07-01",
            cd_servidor=1001,
            cd_situacaoprotocolo=situacao.cd_situacaoprotocolo,
        )
        self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao())

        response = self.cliente_medico.get("/api/v1/apoio/atendimentos")

        self.assertEqual(response.json()[0]["situacao_protocolo"], "Em analise")

    def test_atendimentos_mostra_parecer_em_rascunho_sem_solicitacao(self) -> None:
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

        response = self.cliente_medico.get("/api/v1/apoio/atendimentos")

        dados = response.json()
        self.assertEqual(len(dados), 1)
        self.assertTrue(dados[0]["parecer_em_aberto"])
        self.assertEqual(dados[0]["parecer_autor"], self.medico.get_username())
        self.assertEqual(dados[0]["apoios"], [])

    def test_atendimentos_some_quando_tudo_e_concluido(self) -> None:
        parecer = criar_parecer(
            ator=self.medico,
            servidor_sismed_id=1001,
            protocolo_sismed_id=None,
            texto="Paciente em observação.",
            conclusao="acompanhamento",
            prioritario=False,
            data_reavaliacao=None,
            concluir=False,
        )
        criada = self._post(self.cliente_medico, "/api/v1/apoio", self._payload_criacao()).json()
        self._post(
            self.cliente_seguranca,
            f"/api/v1/apoio/{criada['id']}/responder",
            {"texto_resposta": "Concluído."},
        )

        ainda_aberto = self.cliente_medico.get("/api/v1/apoio/atendimentos").json()
        self.assertEqual(len(ainda_aberto), 1)
        self.assertTrue(ainda_aberto[0]["parecer_em_aberto"])
        self.assertEqual(ainda_aberto[0]["apoios"][0]["estado"], "respondida")

        concluir_parecer(ator=self.medico, parecer=parecer)

        response = self.cliente_medico.get("/api/v1/apoio/atendimentos")
        self.assertEqual(response.json(), [])

    def test_atendimentos_continua_visivel_se_sobrar_solicitacao_aberta(self) -> None:
        parecer = criar_parecer(
            ator=self.medico,
            servidor_sismed_id=1001,
            protocolo_sismed_id=None,
            texto="Paciente em observação.",
            conclusao="acompanhamento",
            prioritario=False,
            data_reavaliacao=None,
            concluir=False,
        )
        self._post(
            self.cliente_medico,
            "/api/v1/apoio",
            self._payload_criacao(especialidade="assistencia_social"),
        )
        concluir_parecer(ator=self.medico, parecer=parecer)

        response = self.cliente_medico.get("/api/v1/apoio/atendimentos")

        dados = response.json()
        self.assertEqual(len(dados), 1)
        self.assertFalse(dados[0]["parecer_em_aberto"])
        self.assertEqual(dados[0]["apoios"][0]["especialidade"], "assistencia_social")
        self.assertEqual(dados[0]["apoios"][0]["estado"], "aberta")

    def test_atendimentos_mostra_pendencia_aberta_por_outro_medico_da_mesma_unidade(self) -> None:
        outro_medico = get_user_model().objects.create_user(
            username="medico.colega",
            password="Senha-ficticia-123",
            unidade=self.medico.unidade,
        )
        outro_medico.groups.add(Group.objects.get(name="Médico"))
        criar_parecer(
            ator=outro_medico,
            servidor_sismed_id=1001,
            protocolo_sismed_id=None,
            texto="Parecer de outro médico.",
            conclusao="acompanhamento",
            prioritario=False,
            data_reavaliacao=None,
            concluir=False,
        )

        response = self.cliente_medico.get("/api/v1/apoio/atendimentos")

        dados = response.json()
        self.assertEqual(len(dados), 1)
        self.assertTrue(dados[0]["parecer_em_aberto"])
        self.assertEqual(dados[0]["parecer_autor"], "medico.colega")

    def test_atendimentos_nao_mostra_pendencia_de_outra_unidade(self) -> None:
        outra_unidade = Unidade.objects.get(codigo="caixa-de-previdencia")
        medico_de_outra_unidade = get_user_model().objects.create_user(
            username="medico.outra.unidade",
            password="Senha-ficticia-123",
            unidade=outra_unidade,
        )
        medico_de_outra_unidade.groups.add(Group.objects.get(name="Médico"))
        criar_parecer(
            ator=medico_de_outra_unidade,
            servidor_sismed_id=1001,
            protocolo_sismed_id=None,
            texto="Parecer de outra unidade.",
            conclusao="acompanhamento",
            prioritario=False,
            data_reavaliacao=None,
            concluir=False,
        )

        response = self.cliente_medico.get("/api/v1/apoio/atendimentos")

        self.assertEqual(response.json(), [])
