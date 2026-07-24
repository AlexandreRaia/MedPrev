from django.db import models
from django.test import SimpleTestCase

from apps.legado.database_router import SisMedDatabaseRouter
from apps.legado.models import (
    SisMedSomenteLeituraError,
    SisMedSomenteLeituraModel,
)


class RegistroLegadoParaTeste(SisMedSomenteLeituraModel):
    nome = models.CharField(max_length=100)

    class Meta:
        app_label = "legado"
        managed = False
        db_table = "registro_legado_para_teste"


class ProtecaoDoSisMedTests(SimpleTestCase):
    def setUp(self) -> None:
        self.router = SisMedDatabaseRouter()

    def test_leitura_e_direcionada_para_alias_sismed(self) -> None:
        self.assertEqual(self.router.db_for_read(RegistroLegadoParaTeste), "sismed")

    def test_router_recusa_escrita(self) -> None:
        with self.assertRaises(SisMedSomenteLeituraError):
            self.router.db_for_write(RegistroLegadoParaTeste)

    def test_modelo_recusa_save(self) -> None:
        registro = RegistroLegadoParaTeste(nome="Dado sintético")

        with self.assertRaises(SisMedSomenteLeituraError):
            registro.save()

    def test_queryset_recusa_update(self) -> None:
        with self.assertRaises(SisMedSomenteLeituraError):
            RegistroLegadoParaTeste.objects.update(nome="Alteração recusada")

    def test_migration_nunca_e_permitida_no_sismed(self) -> None:
        self.assertFalse(
            self.router.allow_migrate(
                database="sismed",
                app_label="qualquer_app",
            )
        )

    def test_relacao_entre_legado_e_medprev_e_recusada(self) -> None:
        from apps.contas.models import Usuario

        registro = RegistroLegadoParaTeste(nome="Dado sintético")
        usuario = Usuario(username="usuario_sintetico")

        self.assertFalse(self.router.allow_relation(registro, usuario))
