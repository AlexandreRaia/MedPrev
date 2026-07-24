from typing import Any

from django.db.models import Model

from apps.legado.models import SisMedSomenteLeituraError

SISMED_DATABASE_ALIAS = "sismed"
SISMED_APP_LABEL = "legado"


class SisMedDatabaseRouter:
    """Direciona leituras legadas e recusa qualquer escrita ou migration."""

    def db_for_read(self, model: type[Model], **hints: Any) -> str | None:
        del hints

        if model._meta.app_label == SISMED_APP_LABEL:
            return SISMED_DATABASE_ALIAS
        return None

    def db_for_write(self, model: type[Model], **hints: Any) -> str | None:
        del hints

        if model._meta.app_label == SISMED_APP_LABEL:
            raise SisMedSomenteLeituraError()
        return None

    def allow_relation(
        self,
        object_one: Model,
        object_two: Model,
        **hints: Any,
    ) -> bool | None:
        del hints

        first_is_legacy = object_one._meta.app_label == SISMED_APP_LABEL
        second_is_legacy = object_two._meta.app_label == SISMED_APP_LABEL

        if first_is_legacy != second_is_legacy:
            return False
        return None

    def allow_migrate(
        self,
        database: str,
        app_label: str,
        model_name: str | None = None,
        **hints: Any,
    ) -> bool | None:
        del model_name, hints

        if database == SISMED_DATABASE_ALIAS or app_label == SISMED_APP_LABEL:
            return False
        return None
