from __future__ import annotations

import json
import re
from typing import Iterable, List, Optional, Sequence

try:
    from agno.tools.sql import SQLTools
except ImportError:  # pragma: no cover - allows parser/tests to run before uv sync
    SQLTools = None  # type: ignore


FORBIDDEN_SQL_PATTERNS = [
    r"\binsert\b",
    r"\bupdate\b",
    r"\bdelete\b",
    r"\bdrop\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bcreate\b",
    r"\breplace\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bcommit\b",
    r"\brollback\b",
    r"\bmerge\b",
    r"\bcall\b",
]


def _strip_sql_comments(query: str) -> str:
    query = re.sub(r"/\*.*?\*/", " ", query, flags=re.S)
    query = re.sub(r"--.*?$", " ", query, flags=re.M)
    return query.strip()


def _normalize_identifier(identifier: str) -> str:
    cleaned = identifier.strip().strip("`").strip('"').strip("'").strip()
    if "." in cleaned:
        cleaned = cleaned.split(".")[-1]
    return cleaned.lower()


def _extract_table_names(query: str) -> List[str]:
    matches = re.findall(r"\b(?:from|join)\s+([`\"A-Za-z0-9_.]+)", query, flags=re.I)
    return [_normalize_identifier(match) for match in matches]


def validate_read_only_sql(query: str, allowed_tables: Iterable[str], default_limit: int = 50) -> str:
    sanitized = _strip_sql_comments(query)
    if not sanitized:
        raise ValueError("Empty SQL query.")

    if sanitized.count(";") > 1 or (";" in sanitized[:-1]):
        raise ValueError("Multiple SQL statements are not allowed.")

    lowered = sanitized.lower()
    if not (lowered.startswith("select") or lowered.startswith("with")):
        raise ValueError("Only SELECT/WITH queries are allowed.")

    for pattern in FORBIDDEN_SQL_PATTERNS:
        if re.search(pattern, lowered):
            raise ValueError("Write or DDL operations are not allowed.")

    allowed = {_normalize_identifier(name) for name in allowed_tables}
    referenced_tables = set(_extract_table_names(sanitized))
    disallowed = sorted(name for name in referenced_tables if name not in allowed)
    if disallowed:
        raise ValueError(f"Query references non-whitelisted tables: {', '.join(disallowed)}")

    if re.search(r"\blimit\s+\d+(\s*,\s*\d+)?\s*;?\s*$", lowered) is None:
        sanitized = sanitized.rstrip(";").rstrip() + f" LIMIT {default_limit}"

    return sanitized


if SQLTools is not None:

    class ReadOnlySQLTools(SQLTools):
        def __init__(
            self,
            db_url: str,
            allowed_tables: Sequence[str],
            default_limit: int = 50,
        ) -> None:
            self.allowed_tables = list(allowed_tables)
            self.default_limit = default_limit
            super().__init__(
                db_url=db_url,
                enable_list_tables=True,
                enable_describe_table=True,
                enable_run_sql_query=True,
            )

        def list_tables(self) -> str:
            return json.dumps(self.allowed_tables, ensure_ascii=False)

        def describe_table(self, table_name: str) -> str:
            normalized = _normalize_identifier(table_name)
            if normalized not in {_normalize_identifier(t) for t in self.allowed_tables}:
                return f"Error getting table schema: table `{table_name}` is not allowed."
            return super().describe_table(table_name)

        def run_sql_query(self, query: str, limit: Optional[int] = None) -> str:
            safe_query = validate_read_only_sql(
                query=query,
                allowed_tables=self.allowed_tables,
                default_limit=limit or self.default_limit,
            )
            return super().run_sql_query(query=safe_query, limit=limit or self.default_limit)

else:

    class ReadOnlySQLTools:  # pragma: no cover
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("Agno is not installed. Run `uv sync` before creating ReadOnlySQLTools.")
