from __future__ import annotations

import difflib
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.agents.router import ask  # noqa: E402
from app.agents.rag_agent import build_rag_agent  # noqa: E402
from app.agents.text_to_sql_agent import build_text_to_sql_agent  # noqa: E402


RESULTS_DIR = PROJECT_ROOT / "data" / "eval"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

QUESTION_SET_PATH = next(
    path for path in PROJECT_ROOT.glob("*.json") if path.name != "test_runs.json"
)

RESULTS_JSONL_PATH = RESULTS_DIR / "full_eval_results.jsonl"
SUMMARY_JSON_PATH = RESULTS_DIR / "full_eval_summary.json"
PROGRESS_JSON_PATH = RESULTS_DIR / "full_eval_progress.json"


def normalize(text: str) -> str:
    replacements = {
        "（": "(",
        "）": ")",
        "，": ",",
        "。": ".",
        "：": ":",
        "；": ";",
        "、": ",",
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
        "％": "%",
        "－": "-",
        "×": "x",
        "㎡": "m2",
        "²": "2",
        "³": "3",
        "·": "",
        "／": "/",
        " ": "",
        "\t": "",
        "\n": "",
        "\r": "",
        "亿m³": "亿m3",
        "m³/s": "m3/s",
        "m³": "m3",
        "km²": "km2",
        "kW·h": "kWh",
        "kw·h": "kwh",
    }
    normalized = text.strip()
    for old, new in replacements.items():
        normalized = normalized.replace(old, new)
    return normalized.lower()


def extract_numbers(text: str) -> set[str]:
    tokens = re.findall(r"\d+(?:\.\d+)?", normalize(text))
    normalized: set[str] = set()
    for token in tokens:
        try:
            normalized.add(format(Decimal(token).normalize(), "f"))
        except InvalidOperation:
            normalized.add(token)
    return normalized


def reference_chunks(text: str) -> list[str]:
    chunks: list[str] = []
    for part in re.split(r"[，。,.;；、:：()（）\s]+", text):
        candidate = part.strip()
        if len(candidate) < 3:
            continue
        if re.fullmatch(r"[\d.x/%a-zA-Z]+", normalize(candidate)):
            continue
        chunks.append(candidate)
    return chunks


def classify(expected: str, actual: str) -> tuple[str, dict[str, Any]]:
    expected_norm = normalize(expected)
    actual_norm = normalize(actual)
    ratio = difflib.SequenceMatcher(None, expected_norm, actual_norm).ratio()
    expected_numbers = extract_numbers(expected)
    actual_numbers = extract_numbers(actual)
    numbers_hit = bool(expected_numbers) and expected_numbers.issubset(actual_numbers)
    chunks = reference_chunks(expected)
    chunk_hit_count = sum(1 for chunk in chunks if normalize(chunk) in actual_norm)
    chunk_hit_ratio = (chunk_hit_count / len(chunks)) if chunks else 0.0

    if expected_norm and (expected_norm in actual_norm or actual_norm in expected_norm):
        verdict = "pass"
    elif numbers_hit and (not chunks or chunk_hit_ratio >= 0.5 or ratio >= 0.45):
        verdict = "pass"
    elif numbers_hit or chunk_hit_count > 0 or ratio >= 0.35:
        verdict = "partial"
    else:
        verdict = "fail"

    metrics = {
        "ratio": round(ratio, 3),
        "numbers_hit": numbers_hit,
        "chunk_hit_count": chunk_hit_count,
        "chunk_total": len(chunks),
        "chunk_hit_ratio": round(chunk_hit_ratio, 3),
    }
    return verdict, metrics


def load_question_set() -> list[dict[str, Any]]:
    data = json.loads(QUESTION_SET_PATH.read_text(encoding="utf-8-sig"))
    rows: list[dict[str, Any]] = []
    index = 0
    for top_name, categories in data.items():
        for category_name, qa_list in categories.items():
            for item in qa_list:
                index += 1
                rows.append(
                    {
                        "index": index,
                        "top_name": top_name,
                        "category_name": category_name,
                        "question": item["question"],
                        "expected": item["answer"],
                    }
                )
    return rows


def load_existing_results() -> dict[int, dict[str, Any]]:
    existing: dict[int, dict[str, Any]] = {}
    if not RESULTS_JSONL_PATH.exists():
        return existing
    for raw_line in RESULTS_JSONL_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        record = json.loads(line)
        existing[int(record["index"])] = record
    return existing


def build_summary(
    questions: list[dict[str, Any]],
    results: dict[int, dict[str, Any]],
    status: str,
    started_at: str,
) -> dict[str, Any]:
    by_top: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass": 0, "partial": 0, "fail": 0, "total": 0}
    )
    by_category: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass": 0, "partial": 0, "fail": 0, "total": 0}
    )
    durations: list[float] = []
    examples: list[dict[str, Any]] = []

    for question in questions:
        result = results.get(question["index"])
        if result is None:
            continue
        verdict = result["verdict"]
        by_top[question["top_name"]]["total"] += 1
        by_top[question["top_name"]][verdict] += 1
        category_key = f"{question['top_name']} / {question['category_name']}"
        by_category[category_key]["total"] += 1
        by_category[category_key][verdict] += 1
        durations.append(float(result["duration_sec"]))
        if verdict != "pass" and len(examples) < 20:
            examples.append(result)

    completed = len(results)
    summary = {
        "question_set_path": str(QUESTION_SET_PATH),
        "results_jsonl_path": str(RESULTS_JSONL_PATH),
        "status": status,
        "started_at": started_at,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "question_count": len(questions),
        "completed_count": completed,
        "remaining_count": len(questions) - completed,
        "pass": sum(item["pass"] for item in by_top.values()),
        "partial": sum(item["partial"] for item in by_top.values()),
        "fail": sum(item["fail"] for item in by_top.values()),
        "avg_duration_sec": round(statistics.mean(durations), 3) if durations else 0.0,
        "max_duration_sec": round(max(durations), 3) if durations else 0.0,
        "by_top": by_top,
        "by_category": by_category,
        "examples": examples,
    }
    return summary


def persist_summary(summary: dict[str, Any]) -> None:
    SUMMARY_JSON_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    PROGRESS_JSON_PATH.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_result(record: dict[str, Any]) -> None:
    with RESULTS_JSONL_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> None:
    started_at = datetime.now().isoformat(timespec="seconds")
    questions = load_question_set()
    results = load_existing_results()

    persist_summary(build_summary(questions, results, "running", started_at))

    for question in questions:
        if question["index"] in results:
            continue

        # Evaluation should treat each question independently. The cached
        # agents are useful for interactive mode, but here they accumulate
        # conversation history and can overflow the model context window.
        build_rag_agent.cache_clear()
        build_text_to_sql_agent.cache_clear()

        started = time.perf_counter()
        exception_message: str | None = None
        try:
            actual = ask(question["question"])
            verdict, metrics = classify(question["expected"], actual)
        except Exception as exc:
            actual = f"EXCEPTION: {type(exc).__name__}: {exc}"
            verdict = "fail"
            metrics = {
                "ratio": 0.0,
                "numbers_hit": False,
                "chunk_hit_count": 0,
                "chunk_total": 0,
                "chunk_hit_ratio": 0.0,
            }
            exception_message = repr(exc)
        duration = round(time.perf_counter() - started, 3)
        record = {
            **question,
            "actual": actual,
            "verdict": verdict,
            "metrics": metrics,
            "duration_sec": duration,
            "finished_at": datetime.now().isoformat(timespec="seconds"),
        }
        if exception_message is not None:
            record["exception"] = exception_message
        results[question["index"]] = record
        append_result(record)
        persist_summary(build_summary(questions, results, "running", started_at))

    persist_summary(build_summary(questions, results, "completed", started_at))


if __name__ == "__main__":
    main()
