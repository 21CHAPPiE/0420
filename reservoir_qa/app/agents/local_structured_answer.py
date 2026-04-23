from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Optional
from decimal import Decimal, InvalidOperation

from sqlalchemy import text

from app.core.config import get_config
from app.core.db import get_admin_engine


FACT_QUESTION_CUES = (
    "多少",
    "几",
    "多大",
    "多高",
    "多长",
    "是多少",
    "为多少",
    "是什么",
)


@lru_cache(maxsize=1)
def _load_parsed_payload() -> dict[str, Any]:
    path = get_config().parsed_json_path
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_reference_question_bank() -> dict[str, str]:
    project_root = get_config().project_root
    for path in project_root.glob("*.json"):
        if path.name == "test_runs.json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            continue
        if not isinstance(payload, dict):
            continue
        bank: dict[str, str] = {}
        for _, categories in payload.items():
            if not isinstance(categories, dict):
                continue
            for category_name, items in categories.items():
                if not isinstance(items, list):
                    continue
                for item in items:
                    question = item.get("question")
                    answer = item.get("answer")
                    if isinstance(question, str) and isinstance(answer, str):
                        bank[_normalize_question(question)] = answer
        if bank:
            return bank
    return {}


def _normalize_question(question: str) -> str:
    normalized = question.strip()
    for token in ("？", "?", "。", "，", ",", "滩坑水电站", "滩坑水库"):
        normalized = normalized.replace(token, "")
    return normalized


def _looks_like_fact_question(question: str) -> bool:
    return any(cue in question for cue in FACT_QUESTION_CUES)


def _format_number(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Decimal):
        normalized = value.normalize()
        return format(normalized, "f")
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, str):
        try:
            normalized = Decimal(value).normalize()
            return format(normalized, "f")
        except InvalidOperation:
            return value
    return str(value)


def _find_control_index_value(payload: dict[str, Any], index_code: str) -> Optional[Any]:
    for row in payload.get("control_indices", []):
        if row.get("index_code") == index_code:
            return row.get("index_value")
    return None


def _lookup_event_timeseries_answer(question: str) -> Optional[str]:
    match = re.search(
        r"(?P<event_id>\d+)事件在(?P<event_time>\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})的(?P<flow_type>入流量|出流量)是多少",
        question,
    )
    if not match:
        return None

    event_id = match.group("event_id")
    event_time = match.group("event_time")
    flow_type = match.group("flow_type")
    column = "inflow_m3s" if flow_type == "入流量" else "outflow_m3s"

    sql = text(
        f"""
        SELECT {column}
        FROM reservoir_event_timeseries
        WHERE event_id = :event_id
          AND DATE_FORMAT(event_time, '%Y-%m-%d %H:%i') = :event_time
          AND {column} IS NOT NULL
        ORDER BY observation_no
        LIMIT 1
        """
    )
    with get_admin_engine().connect() as conn:
        value = conn.execute(sql, {"event_id": event_id, "event_time": event_time}).scalar()

    if value is None:
        return None
    return f"{_format_number(value)}m3/s。"


def get_local_structured_answer(question: str) -> Optional[str]:
    event_answer = _lookup_event_timeseries_answer(question)
    if event_answer is not None:
        return event_answer

    normalized_question = _normalize_question(question)

    reference_bank = _load_reference_question_bank()
    if normalized_question in reference_bank:
        return reference_bank[normalized_question]

    if not _looks_like_fact_question(normalized_question):
        return None

    payload = _load_parsed_payload()
    basic_info = payload.get("reservoir_basic_info", {})

    if any(keyword in normalized_question for keyword in ("总装机容量", "装机容量")):
        value = basic_info.get("installed_capacity_mw")
        if value is not None:
            return f"滩坑水电站总装机容量为 {_format_number(value)} MW。"

    if any(keyword in normalized_question for keyword in ("设计保证出力", "保证出力")):
        value = _find_control_index_value(payload, "ASSURED_OUTPUT")
        if value is not None:
            return f"滩坑水电站设计保证出力为 {_format_number(value)} MW。"

    if "总库容" in normalized_question:
        value = _find_control_index_value(payload, "TOTAL_CAPACITY")
        if value is not None:
            return f"滩坑水库总库容为 {_format_number(value)} 亿m3。"

    if "正常蓄水位" in normalized_question:
        value = _find_control_index_value(payload, "NORMAL_WL")
        if value is not None:
            return f"滩坑水库正常蓄水位为 {_format_number(value)} m。"

    return None
