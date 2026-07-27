import sqlite3
from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.db import connection, models
from django.test import Client, SimpleTestCase, TestCase

from apps.legado.dump_importer import (
    create_table_sql,
    normalize_value,
    parse_constraints,
    parse_table_definition,
)
from apps.legado.models import (
    Licenca,
    Pericia,
    Protocolo,
    Servidor,
    SituacaoProtocolo,
    TabelaImportadaModel,
)
from apps.legado.selectors import (
    buscar_servidores,
    descricoes_das_situacoes,
    pericias_do_protocolo,
    protocolos_do_servidor,
)


class RegistroImportadoParaTeste(TabelaImportadaModel):
    nome = models.CharField(max_length=100)

    class Meta:
        app_label = "legado"
        managed = False
        db_table = "registro_importado_para_teste"


class MapeamentoDasTabelasFicticiasTests(SimpleTestCase):
    def test_tabelas_prioritarias_usam_o_banco_padrao(self) -> None:
        modelos_e_tabelas = [
            (Servidor, "servidor", "cd_servidor"),
            (Protocolo, "protocolo", "cd_protocolo"),
            (
                SituacaoProtocolo,
                "situacaoprotocolo",
                "cd_situacaoprotocolo",
            ),
            (Licenca, "licenca", "cd_licenca"),
            (Pericia, "pericia", "cd_pericia"),
        ]

        for modelo, tabela, chave_primaria in modelos_e_tabelas:
            with self.subTest(modelo=modelo.__name__):
                self.assertFalse(modelo._meta.managed)
                self.assertEqual(modelo._meta.db_table, tabela)
                self.assertEqual(modelo._meta.pk.name, chave_primaria)
                self.assertEqual(modelo.objects.db, "default")

    def test_modelos_nao_bloqueiam_escrita(self) -> None:
        self.assertIs(RegistroImportadoParaTeste.save, models.Model.save)
        self.assertIs(RegistroImportadoParaTeste.delete, models.Model.delete)

    def test_referencias_ainda_sao_ids_escalares(self) -> None:
        referencias = [
            (Protocolo, "cd_servidor"),
            (Protocolo, "cd_licenca"),
            (Protocolo, "cd_situacaoprotocolo"),
            (Pericia, "cd_protocolo"),
            (Pericia, "cd_licenca"),
            (Pericia, "cd_profissional"),
        ]

        for modelo, campo in referencias:
            with self.subTest(modelo=modelo.__name__, campo=campo):
                self.assertFalse(modelo._meta.get_field(campo).is_relation)


class SelectorsDosDadosFicticiosTests(SimpleTestCase):
    def test_busca_vazia_nao_retorna_todo_o_cadastro(self) -> None:
        queryset = buscar_servidores("   ")

        self.assertEqual(queryset.db, "default")
        self.assertTrue(queryset.query.is_empty())

    def test_busca_de_servidor_tem_limite_seguro(self) -> None:
        queryset = buscar_servidores("Servidor", limite=500)

        self.assertEqual(queryset.db, "default")
        self.assertEqual(queryset.query.high_mark, 100)
        self.assertEqual(queryset.query.order_by, ("nm_servidor", "cd_servidor"))

    def test_protocolos_incluem_todos_os_status(self) -> None:
        queryset = protocolos_do_servidor(1001)

        self.assertEqual(queryset.db, "default")
        self.assertEqual(queryset.query.order_by, ("-dt_protocolo", "-cd_protocolo"))

    def test_pericias_sao_ordenadas_da_mais_recente(self) -> None:
        queryset = pericias_do_protocolo(1)

        self.assertEqual(queryset.db, "default")
        self.assertEqual(queryset.query.order_by, ("-dt_pericia", "-cd_pericia"))


class ConversorDoDumpTests(SimpleTestCase):
    def setUp(self) -> None:
        self.table = parse_table_definition(
            """
CREATE TABLE dbo.exemplo (
    cd_exemplo bigint NOT NULL,
    ds_exemplo text,
    st_ativo boolean DEFAULT true NOT NULL
);
""".strip()
        )

    def test_converte_tipos_e_chave_primaria_para_sqlite(self) -> None:
        entries = [
            SimpleNamespace(
                defn=(
                    "ALTER TABLE ONLY dbo.exemplo\n"
                    "    ADD CONSTRAINT pk_exemplo PRIMARY KEY (cd_exemplo);"
                )
            )
        ]
        constraints = parse_constraints(entries)
        sql = create_table_sql(self.table, constraints["exemplo"])

        connection = sqlite3.connect(":memory:")
        connection.execute(sql)
        connection.execute(
            "INSERT INTO exemplo (ds_exemplo) VALUES (?)",
            ("Registro fictício",),
        )
        row = connection.execute("SELECT cd_exemplo, ds_exemplo, st_ativo FROM exemplo").fetchone()
        connection.close()

        self.assertEqual(row, (1, "Registro fictício", 1))

    def test_normaliza_booleanos_do_postgresql(self) -> None:
        boolean_column = self.table.columns[2]

        self.assertEqual(normalize_value("t", boolean_column), 1)
        self.assertEqual(normalize_value("f", boolean_column), 0)


class ApiDeServidoresTests(TestCase):
    """
    As tabelas legadas são managed=False e não existem no banco de teste por
    migration. Aqui a estrutura é criada manualmente antes de a classe abrir
    sua transação de teste, apenas para simular dados fictícios já
    importados; o SQLite exige que a criação ocorra fora de uma transação.
    """

    @classmethod
    def setUpClass(cls) -> None:
        with connection.schema_editor() as editor:
            editor.create_model(Servidor)
            editor.create_model(SituacaoProtocolo)
            editor.create_model(Protocolo)
            editor.create_model(Pericia)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(Pericia)
            editor.delete_model(Protocolo)
            editor.delete_model(SituacaoProtocolo)
            editor.delete_model(Servidor)

    def setUp(self) -> None:
        usuario_model = get_user_model()
        self.usuario = usuario_model.objects.create_user(
            username="operador.teste",
            password="Senha-ficticia-123",
        )
        self.usuario.groups.add(Group.objects.get(name="Operador Administrativo"))
        self.cliente = Client()
        self.cliente.force_login(self.usuario)

        Servidor.objects.create(
            cd_servidor=1001,
            nm_servidor="Maria da Silva",
            nro_cpf="123.456.789-00",
            dt_nascimento="1988-07-04",
            cd_funcao=1,
            cd_vinculo=1,
            cd_secretaria=1,
            cd_departamento=1,
            dt_admissao="2020-01-01",
            cd_situacao=1,
            st_ativo=True,
            ds_email="maria@example.test",
            nro_telefone="1140000000",
            nro_celular="11999990000",
        )
        SituacaoProtocolo.objects.create(
            cd_situacaoprotocolo=1,
            ds_situacaoprotocolo="Em andamento",
            st_ativo=True,
        )
        Protocolo.objects.create(
            cd_protocolo=1,
            dt_protocolo="2024-03-01",
            cd_servidor=1001,
            cd_situacaoprotocolo=1,
        )
        Pericia.objects.create(
            cd_pericia=1,
            cd_protocolo=1,
            dt_pericia="2024-03-05",
            ds_subjetivo="Paciente relata dor lombar recorrente.",
            ds_objetivo="Exame clínico sem alterações agudas.",
            ds_conduta="Encaminhado para acompanhamento.",
            ic_atestado="t",
            qt_atestadodias=15,
        )

    def test_recusa_usuario_nao_autenticado(self) -> None:
        response = Client().get("/api/v1/legado/servidores?busca=Maria")

        self.assertEqual(response.status_code, 401)

    def test_recusa_usuario_sem_permissao_de_consulta(self) -> None:
        sem_permissao = get_user_model().objects.create_user(
            username="sem.permissao",
            password="Senha-ficticia-123",
        )
        cliente = Client()
        cliente.force_login(sem_permissao)

        response = cliente.get("/api/v1/legado/servidores?busca=Maria")

        self.assertEqual(response.status_code, 403)

    def test_busca_vazia_nao_retorna_registros(self) -> None:
        response = self.cliente.get("/api/v1/legado/servidores")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_busca_por_nome_retorna_servidor_correspondente(self) -> None:
        response = self.cliente.get("/api/v1/legado/servidores?busca=Maria")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(len(dados), 1)
        self.assertEqual(dados[0]["id"], 1001)
        self.assertEqual(dados[0]["nome"], "Maria da Silva")
        self.assertEqual(dados[0]["email"], "maria@example.test")

    def test_detalhe_inclui_protocolos_com_situacao_descrita(self) -> None:
        response = self.cliente.get("/api/v1/legado/servidores/1001")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertEqual(dados["email"], "maria@example.test")
        self.assertEqual(dados["nascimento"], "1988-07-04")
        self.assertEqual(len(dados["protocolos"]), 1)
        self.assertEqual(dados["protocolos"][0]["situacao"], "Em andamento")

    def test_detalhe_oculta_historico_medico_sem_a_permissao_especifica(self) -> None:
        response = self.cliente.get("/api/v1/legado/servidores/1001")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertFalse(dados["historico_medico_visivel"])
        self.assertEqual(dados["pericias"], [])

    def test_detalhe_inclui_historico_medico_com_a_permissao_especifica(self) -> None:
        self.usuario.groups.add(Group.objects.get(name="Médico do Trabalho"))

        response = self.cliente.get("/api/v1/legado/servidores/1001")

        self.assertEqual(response.status_code, 200)
        dados = response.json()
        self.assertTrue(dados["historico_medico_visivel"])
        self.assertEqual(len(dados["pericias"]), 1)
        self.assertEqual(
            dados["pericias"][0]["subjetivo"],
            "Paciente relata dor lombar recorrente.",
        )
        self.assertEqual(
            dados["pericias"][0]["conduta"],
            "Encaminhado para acompanhamento.",
        )
        self.assertTrue(dados["pericias"][0]["atestado"])
        self.assertEqual(dados["pericias"][0]["dias_atestado"], 15)

    def test_detalhe_de_servidor_inexistente_retorna_404(self) -> None:
        response = self.cliente.get("/api/v1/legado/servidores/9999")

        self.assertEqual(response.status_code, 404)


class SelectorDeDescricoesDeSituacaoTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        with connection.schema_editor() as editor:
            editor.create_model(SituacaoProtocolo)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        with connection.schema_editor() as editor:
            editor.delete_model(SituacaoProtocolo)

    def test_mapeia_ids_para_descricoes_ignorando_ausentes(self) -> None:
        SituacaoProtocolo.objects.create(
            cd_situacaoprotocolo=1,
            ds_situacaoprotocolo="Em andamento",
            st_ativo=True,
        )

        resultado = descricoes_das_situacoes([1, None, 999])

        self.assertEqual(resultado, {1: "Em andamento"})

    def test_lista_vazia_nao_consulta_o_banco(self) -> None:
        self.assertEqual(descricoes_das_situacoes([]), {})
