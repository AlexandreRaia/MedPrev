import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pgdumplib

IDENTIFIER_PATTERN = r"[A-Za-z_][A-Za-z0-9_]*"
SUPPORTED_TYPES = (
    "timestamp with time zone",
    "bigint",
    "integer",
    "boolean",
    "numeric",
    "date",
    "text",
)
SQLITE_TYPES = {
    "bigint": "INTEGER",
    "integer": "INTEGER",
    "boolean": "INTEGER",
    "numeric": "NUMERIC",
    "date": "TEXT",
    "text": "TEXT",
    "timestamp with time zone": "TEXT",
}
DJANGO_TABLE_PREFIXES = ("auth_", "django_", "contas_")
DJANGO_TABLE_NAMES = {"sqlite_sequence"}


@dataclass(frozen=True)
class Column:
    name: str
    postgres_type: str
    nullable: bool
    default: str | None


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[Column, ...]


def quote_identifier(identifier: str) -> str:
    if not re.fullmatch(IDENTIFIER_PATTERN, identifier):
        raise ValueError(f"Identificador SQL inválido: {identifier!r}")
    return f'"{identifier}"'


def parse_table_definition(definition: str) -> Table:
    header = re.search(
        rf"CREATE TABLE dbo\.({IDENTIFIER_PATTERN})\s*\(",
        definition,
        re.IGNORECASE,
    )
    if not header:
        raise ValueError(f"Definição de tabela não reconhecida:\n{definition}")

    columns: list[Column] = []
    type_pattern = "|".join(re.escape(item) for item in SUPPORTED_TYPES)
    column_pattern = re.compile(
        rf"^\s*({IDENTIFIER_PATTERN})\s+({type_pattern})(.*?)[,]?\s*$",
        re.IGNORECASE,
    )

    for line in definition.splitlines()[1:-1]:
        match = column_pattern.match(line)
        if not match:
            raise ValueError(f"Definição de coluna não reconhecida: {line!r}")

        name, postgres_type, options = match.groups()
        default_match = re.search(
            r"\bDEFAULT\s+(.+?)(?=\s+NOT NULL\b|$)",
            options,
            re.IGNORECASE,
        )
        columns.append(
            Column(
                name=name,
                postgres_type=postgres_type.lower(),
                nullable="NOT NULL" not in options.upper(),
                default=default_match.group(1).strip() if default_match else None,
            )
        )

    return Table(name=header.group(1), columns=tuple(columns))


def parse_constraints(entries: list[Any]) -> dict[str, list[str]]:
    constraints: dict[str, list[str]] = {}
    pattern = re.compile(
        rf"ALTER TABLE ONLY dbo\.({IDENTIFIER_PATTERN})\s+"
        rf"ADD CONSTRAINT ({IDENTIFIER_PATTERN})\s+(.+);",
        re.IGNORECASE | re.DOTALL,
    )

    for entry in entries:
        match = pattern.fullmatch(entry.defn.strip())
        if not match:
            raise ValueError(f"Restrição não reconhecida:\n{entry.defn}")

        table_name, constraint_name, clause = match.groups()
        clause = re.sub(
            rf"REFERENCES dbo\.({IDENTIFIER_PATTERN})",
            lambda item: f"REFERENCES {quote_identifier(item.group(1))}",
            clause,
            flags=re.IGNORECASE,
        )
        clause = re.sub(
            rf"\b({IDENTIFIER_PATTERN})\b(?=\s*(?:,|\)))",
            lambda item: quote_identifier(item.group(1)),
            clause,
        )
        constraints.setdefault(table_name, []).append(
            f"CONSTRAINT {quote_identifier(constraint_name)} {clause}"
        )

    return constraints


def sqlite_default(default: str | None) -> str | None:
    if default is None or "nextval(" in default.lower():
        return None
    if default.lower() in {"true", "false"}:
        return "1" if default.lower() == "true" else "0"

    text_cast = re.fullmatch(r"'(.*)'::text", default, re.DOTALL)
    if text_cast:
        value = text_cast.group(1).replace("'", "''")
        return f"'{value}'"

    raise ValueError(f"Valor padrão PostgreSQL não suportado: {default}")


def create_table_sql(table: Table, constraints: list[str]) -> str:
    definitions = []
    for column in table.columns:
        parts = [
            quote_identifier(column.name),
            SQLITE_TYPES[column.postgres_type],
        ]
        default = sqlite_default(column.default)
        if default is not None:
            parts.extend(("DEFAULT", default))
        if not column.nullable:
            parts.append("NOT NULL")
        definitions.append(" ".join(parts))

    definitions.extend(constraints)
    body = ",\n    ".join(definitions)
    return f"CREATE TABLE {quote_identifier(table.name)} (\n    {body}\n)"


def normalize_value(value: Any, column: Column) -> Any:
    if value is None:
        return None
    if column.postgres_type == "boolean":
        if value in (True, "t", "true", "1", 1):
            return 1
        if value in (False, "f", "false", "0", 0):
            return 0
        raise ValueError(f"Booleano inválido na coluna {column.name}: {value!r}")
    if column.postgres_type in {"bigint", "integer"}:
        return int(value)
    if column.postgres_type == "numeric":
        return str(value)
    return value


def is_protected_django_table(table_name: str) -> bool:
    return table_name in DJANGO_TABLE_NAMES or table_name.startswith(DJANGO_TABLE_PREFIXES)


def import_dump_to_sqlite(
    *,
    dump_path: Path,
    sqlite_path: Path,
    replace: bool = False,
) -> dict[str, int]:
    dump = pgdumplib.load(str(dump_path))
    table_entries = [
        entry for entry in dump.entries if entry.desc == "TABLE" and entry.namespace == "dbo"
    ]
    tables = [parse_table_definition(entry.defn) for entry in table_entries]

    protected = [table.name for table in tables if is_protected_django_table(table.name)]
    if protected:
        raise ValueError(
            "O dump tenta sobrescrever tabelas protegidas do Django: "
            + ", ".join(sorted(protected))
        )

    constraint_entries = [
        entry
        for entry in dump.entries
        if entry.desc in {"CONSTRAINT", "FK CONSTRAINT"} and entry.namespace == "dbo"
    ]
    constraints = parse_constraints(constraint_entries)
    counts: dict[str, int] = {}

    connection = sqlite3.connect(sqlite_path)
    connection.execute("PRAGMA foreign_keys = OFF")
    try:
        existing = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        collisions = sorted(existing.intersection(table.name for table in tables))
        if collisions and not replace:
            raise ValueError(
                "Estas tabelas já existem: "
                + ", ".join(collisions)
                + ". Use --replace para recriar somente as tabelas importadas."
            )

        connection.execute("BEGIN")
        if replace:
            for table in reversed(tables):
                connection.execute(f"DROP TABLE IF EXISTS {quote_identifier(table.name)}")

        for table in tables:
            connection.execute(create_table_sql(table, constraints.get(table.name, [])))
            rows = [
                tuple(
                    normalize_value(value, column)
                    for value, column in zip(row, table.columns, strict=True)
                )
                for row in dump.table_data("dbo", table.name)
            ]
            if rows:
                column_names = ", ".join(quote_identifier(column.name) for column in table.columns)
                placeholders = ", ".join("?" for _ in table.columns)
                connection.executemany(
                    f"INSERT INTO {quote_identifier(table.name)} "
                    f"({column_names}) VALUES ({placeholders})",
                    rows,
                )
            counts[table.name] = len(rows)

        connection.commit()
        connection.execute("PRAGMA foreign_keys = ON")
        violations = list(connection.execute("PRAGMA foreign_key_check"))
        if violations:
            preview = ", ".join(str(item) for item in violations[:5])
            raise ValueError(
                f"A cópia foi criada, mas há {len(violations)} violações "
                f"de chave estrangeira. Primeiras ocorrências: {preview}"
            )
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()

    return counts
