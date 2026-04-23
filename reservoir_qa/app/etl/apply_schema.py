from __future__ import annotations

from pathlib import Path

from sqlalchemy import text

from app.core.config import get_config
from app.core.db import get_admin_server_engine


def _split_sql_statements(sql_text: str) -> list[str]:
    statements = []
    current = []
    in_single = False
    in_double = False
    for char in sql_text:
        if char == "'" and not in_double:
            in_single = not in_single
        elif char == '"' and not in_single:
            in_double = not in_double
        if char == ";" and not in_single and not in_double:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            continue
        current.append(char)
    tail = "".join(current).strip()
    if tail:
        statements.append(tail)
    return statements


def apply_sql_file(path: Path) -> None:
    sql_text = path.read_text(encoding="utf-8")
    statements = _split_sql_statements(sql_text)
    engine = get_admin_server_engine()
    with engine.begin() as conn:
        for statement in statements:
            conn.execute(text(statement))


def apply_default_schema() -> None:
    config = get_config()
    apply_sql_file(config.sql_dir / "001_schema.sql")
    apply_sql_file(config.sql_dir / "002_create_readonly_user.sql")


if __name__ == "__main__":
    apply_default_schema()
    print("Schema applied.")
