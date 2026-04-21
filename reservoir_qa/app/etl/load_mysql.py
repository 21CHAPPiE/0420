from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from sqlalchemy import text

from app.core.db import get_admin_engine
from app.core.config import get_config


TABLE_INSERT_ORDER = [
    ("reservoir_basic_info", "reservoir_basic_info"),
    ("control_indices", "reservoir_control_index"),
    ("period_rules", "reservoir_period_rule"),
    ("dispatch_rules", "reservoir_dispatch_rule"),
    ("dispatch_authority_rules", "reservoir_dispatch_authority_rule"),
    ("monthly_operation_plan", "reservoir_monthly_operation_plan"),
    ("warning_rules", "reservoir_warning_rule"),
    ("gate_operation_rules", "spillway_gate_operation_rule"),
    ("annual_operation_stats", "reservoir_annual_operation_stat"),
    ("gate_operation_log", "reservoir_gate_operation_log"),
    ("flood_forecast_stats", "reservoir_flood_forecast_stat"),
    ("contact_directory", "reservoir_contact_directory"),
    ("engineering_characteristics", "reservoir_engineering_characteristic"),
]


def _load_json() -> dict:
    config = get_config()
    path = Path(config.parsed_json_path)
    if not path.exists():
        raise FileNotFoundError(f"Parsed JSON not found: {path}. Run `parse-pdf` first.")
    return json.loads(path.read_text(encoding="utf-8"))


def _inject_common_fields(records: Iterable[dict]) -> List[dict]:
    result = []
    for row in records:
        item = dict(row)
        item.setdefault("reservoir_code", "TANKENG")
        item.setdefault("source_doc", "tankeng_2025_plan.pdf")
        if "rule_year" not in item and ("warning_code" in item or "authority_code" in item or "rule_code" in item):
            item["rule_year"] = 2025
        if "valid_year" not in item and "index_code" in item:
            item["valid_year"] = 2025
        if "plan_year" not in item and "plan_month" in item:
            item["plan_year"] = 2025
        result.append(item)
    return result


def _insert_rows(table_name: str, rows: List[dict]) -> None:
    if not rows:
        return
    engine = get_admin_engine()
    with engine.begin() as conn:
        for row in rows:
            columns = list(row.keys())
            values_clause = ", ".join(f":{name}" for name in columns)
            columns_clause = ", ".join(columns)
            sql = text(f"INSERT INTO {table_name} ({columns_clause}) VALUES ({values_clause})")
            conn.execute(sql, row)


def load_mysql_from_parsed_json() -> None:
    payload = _load_json()
    for json_key, table_name in TABLE_INSERT_ORDER:
        data = payload[json_key]
        rows = [data] if isinstance(data, dict) else list(data)
        _insert_rows(table_name, _inject_common_fields(rows))


if __name__ == "__main__":
    load_mysql_from_parsed_json()
    print("MySQL load complete.")

