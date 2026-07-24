import sqlite3
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.legado.dump_importer import import_dump_to_sqlite


class Command(BaseCommand):
    help = (
        "Importa a estrutura e os dados fictícios do dump PostgreSQL para o "
        "db.sqlite3 usado no desenvolvimento."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dump",
            type=Path,
            default=settings.BASE_DIR.parent / "sismed.dump",
            help="Caminho do arquivo de dump (padrão: ../sismed.dump).",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Recria somente as tabelas anteriormente importadas.",
        )

    def handle(self, *args, **options) -> None:
        del args
        database = settings.DATABASES["default"]
        if database["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("Este comando é exclusivo da cópia SQLite de desenvolvimento.")

        dump_path = options["dump"].resolve()
        sqlite_path = Path(database["NAME"]).resolve()
        if not dump_path.is_file():
            raise CommandError(f"Dump não encontrado: {dump_path}")

        self.stdout.write(f"Importando {dump_path.name} para {sqlite_path.name}...")
        try:
            counts = import_dump_to_sqlite(
                dump_path=dump_path,
                sqlite_path=sqlite_path,
                replace=options["replace"],
            )
        except (OSError, ValueError, sqlite3.Error) as error:
            raise CommandError(str(error)) from error

        total_rows = sum(counts.values())
        self.stdout.write(
            self.style.SUCCESS(
                f"Cópia concluída: {len(counts)} tabelas e {total_rows} registros fictícios."
            )
        )
