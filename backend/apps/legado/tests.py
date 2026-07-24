import sqlite3
from types import SimpleNamespace

from django.db import models
from django.test import SimpleTestCase

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
