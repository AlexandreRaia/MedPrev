from typing import Any, NoReturn

from django.db import models


class SisMedSomenteLeituraError(RuntimeError):
    def __init__(self) -> None:
        super().__init__(
            "Operação recusada: o SisMed é uma fonte externa estritamente somente leitura."
        )


class SisMedSomenteLeituraQuerySet(models.QuerySet):
    """QuerySet que mantém disponíveis apenas operações de leitura."""

    @staticmethod
    def _recusar_escrita() -> NoReturn:
        raise SisMedSomenteLeituraError()

    def create(self, **kwargs: Any) -> NoReturn:
        del kwargs
        self._recusar_escrita()

    def bulk_create(self, objects: Any, **kwargs: Any) -> NoReturn:
        del objects, kwargs
        self._recusar_escrita()

    def bulk_update(self, objects: Any, fields: Any, **kwargs: Any) -> NoReturn:
        del objects, fields, kwargs
        self._recusar_escrita()

    def update(self, **kwargs: Any) -> NoReturn:
        del kwargs
        self._recusar_escrita()

    def delete(self) -> NoReturn:
        self._recusar_escrita()

    def get_or_create(self, defaults: Any = None, **kwargs: Any) -> NoReturn:
        del defaults, kwargs
        self._recusar_escrita()

    def update_or_create(
        self,
        defaults: Any = None,
        create_defaults: Any = None,
        **kwargs: Any,
    ) -> NoReturn:
        del defaults, create_defaults, kwargs
        self._recusar_escrita()


class SisMedSomenteLeituraModel(models.Model):
    """
    Base para modelos legados.

    Todo modelo concreto também deve declarar ``managed = False`` e o nome real
    da tabela no SisMed.
    """

    objects = SisMedSomenteLeituraQuerySet.as_manager()

    class Meta:
        abstract = True
        managed = False

    def save(self, *args: Any, **kwargs: Any) -> NoReturn:
        del args, kwargs
        raise SisMedSomenteLeituraError()

    def delete(self, *args: Any, **kwargs: Any) -> NoReturn:
        del args, kwargs
        raise SisMedSomenteLeituraError()
