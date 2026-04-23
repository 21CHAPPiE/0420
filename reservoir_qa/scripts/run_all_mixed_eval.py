from __future__ import annotations

import argparse
import difflib
import json
import random
import re
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from app.agents.rag_agent import build_rag_agent  # noqa: E402
from app.agents.router import ask  # noqa: E402
from app.agents.text_to_sql_agent import build_text_to_sql_agent  # noqa: E402
from app.core.db import get_admin_engine  # noqa: E402


RESULTS_DIR = PROJECT_ROOT / "data" / "eval"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
JSONL_PATH = RESULTS_DIR / "all_mixed_eval_results.jsonl"
SUMMARY_PATH = RESULTS_DIR / "all_mixed_eval_results.json"
PROGRESS_PATH = RESULTS_DIR / "all_mixed_eval_progress.json"


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
    values: set[str] = set()
    for token in re.findall(r"\d+(?:\.\d+)?", normalize(text)):
        try:
            values.add(format(Decimal(token).normalize(), "f"))
        except InvalidOperation:
            values.add(token)
    return values


def classify(expected: str, actual_answer: str) -> tuple[str, dict[str, Any]]:
    expected_norm = normalize(expected)
    actual_norm = normalize(actual_answer)
    ratio = difflib.SequenceMatcher(None, expected_norm, actual_norm).ratio()
    expected_numbers = extract_numbers(expected)
    actual_numbers = extract_numbers(actual_answer)
    numbers_hit = bool(expected_numbers) and expected_numbers.issubset(actual_numbers)

    if expected_norm and (expected_norm in actual_norm or actual_norm in expected_norm):
        verdict = "pass"
    elif numbers_hit:
        verdict = "pass"
    elif ratio >= 0.35 or bool(expected_numbers & actual_numbers):
        verdict = "partial"
    else:
        verdict = "fail"

    return verdict, {
        "ratio": round(ratio, 3),
        "numbers_hit": numbers_hit,
        "expected_numbers": sorted(expected_numbers),
        "actual_numbers": sorted(actual_numbers),
    }


def load_question_bank_sample(sample_per_category: int, rng: random.Random) -> list[dict[str, Any]]:
    question_path = next(path for path in PROJECT_ROOT.glob("*.json") if path.name != "test_runs.json")
    payload = json.loads(question_path.read_text(encoding="utf-8-sig"))
    rows: list[dict[str, Any]] = []
    for top_name, categories in payload.items():
        for category_name, items in categories.items():
            item_list = list(items)
            sample_count = min(sample_per_category, len(item_list))
            sampled = rng.sample(item_list, sample_count)
            for item in sampled:
                rows.append(
                    {
                        "source": "question_bank",
                        "top_name": top_name,
                        "category_name": category_name,
                        "question": item["question"],
                        "expected": item["answer"],
                    }
                )
    return rows


def _fmt_decimal(value: Any) -> str:
    if value is None:
        return ""
    dec = Decimal(str(value))
    return format(dec.normalize(), "f")


def load_event_flow_questions(sample_count: int, rng: random.Random) -> list[dict[str, Any]]:
    sql = text(
        """
        SELECT event_id, event_time, inflow_m3s, outflow_m3s
        FROM reservoir_event_timeseries
        WHERE inflow_m3s IS NOT NULL OR outflow_m3s IS NOT NULL
        ORDER BY event_id, observation_no
        """
    )
    with get_admin_engine().connect() as conn:
        records = [dict(row._mapping) for row in conn.execute(sql).fetchall()]

    candidates: list[dict[str, Any]] = []
    for row in records:
        event_id = row["event_id"]
        event_time = row["event_time"].strftime("%Y-%m-%d %H:%M")
        if row.get("inflow_m3s") is not None:
            value = _fmt_decimal(row["inflow_m3s"])
            candidates.append(
                {
                    "source": "event_timeseries",
                    "top_name": "reservoir_event_timeseries",
                    "category_name": "event_inflow",
                    "question": f"{event_id}事件在{event_time}的入流量是多少？",
                    "expected": f"{value}m3/s。",
                }
            )
        if row.get("outflow_m3s") is not None:
            value = _fmt_decimal(row["outflow_m3s"])
            candidates.append(
                {
                    "source": "event_timeseries",
                    "top_name": "reservoir_event_timeseries",
                    "category_name": "event_outflow",
                    "question": f"{event_id}事件在{event_time}的出流量是多少？",
                    "expected": f"{value}m3/s。",
                }
            )

    return rng.sample(candidates, min(sample_count, len(candidates)))


def parse_answer_payload(raw: str) -> str:
    try:
        payload = json.loads(raw)
        data = payload.get("data") if isinstance(payload, dict) else None
        if isinstance(data, dict) and isinstance(data.get("answer"), str):
            return data["answer"]
    except Exception:
        pass
    return raw


def append_jsonl(record: dict[str, Any]) -> None:
    with JSONL_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def load_existing_results() -> list[dict[str, Any]]:
    if not JSONL_PATH.exists():
        return []
    records: list[dict[str, Any]] = []
    for raw_line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line:
            records.append(json.loads(line))
    return records


def persist_summary(payload: dict[str, Any]) -> None:
    SUMMARY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    PROGRESS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_eval(
    rows: list[dict[str, Any]],
    existing: list[dict[str, Any]],
    *,
    per_category: int,
    event_samples: int,
    seed: int,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = list(existing)
    done_keys = {(r["source"], r["category_name"], r["question"]) for r in existing}
    next_index = len(results) + 1
    for row in rows:
        row_key = (row["source"], row["category_name"], row["question"])
        if row_key in done_keys:
            continue
        build_rag_agent.cache_clear()
        build_text_to_sql_agent.cache_clear()

        started = time.perf_counter()
        exception: str | None = None
        try:
            raw_actual = ask(row["question"])
            actual_answer = parse_answer_payload(raw_actual)
            verdict, metrics = classify(row["expected"], actual_answer)
        except Exception as exc:
            raw_actual = ""
            actual_answer = f"EXCEPTION: {type(exc).__name__}: {exc}"
            verdict = "fail"
            metrics = {"ratio": 0.0, "numbers_hit": False}
            exception = repr(exc)

        duration = round(time.perf_counter() - started, 3)
        record = {
            "index": next_index,
            **row,
            "actual": actual_answer,
            "raw_actual": raw_actual,
            "verdict": verdict,
            "metrics": metrics,
            "duration_sec": duration,
            "finished_at": datetime.now().isoformat(timespec="seconds"),
        }
        if exception:
            record["exception"] = exception
        results.append(record)
        append_jsonl(record)
        payload = {
            "created_at": datetime.now().isoformat(timespec="seconds"),
            "seed": seed,
            "per_category": per_category,
            "event_samples": event_samples,
            "summary": summarize(results),
            "results": results,
        }
        payload["result_path"] = str(SUMMARY_PATH)
        persist_summary(payload)
        next_index += 1
        print(
            f"[{len(results)}/{len(rows)}] {row['category_name']} | "
            f"{verdict} | {duration}s"
        )
    return results


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    by_category: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass": 0, "partial": 0, "fail": 0, "total": 0}
    )
    by_source: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass": 0, "partial": 0, "fail": 0, "total": 0}
    )
    durations = []
    for result in results:
        verdict = result["verdict"]
        category_key = f"{result['top_name']} / {result['category_name']}"
        by_category[category_key]["total"] += 1
        by_category[category_key][verdict] += 1
        by_source[result["source"]]["total"] += 1
        by_source[result["source"]][verdict] += 1
        durations.append(result["duration_sec"])

    return {
        "sample_count": len(results),
        "pass": sum(item["pass"] for item in by_source.values()),
        "partial": sum(item["partial"] for item in by_source.values()),
        "fail": sum(item["fail"] for item in by_source.values()),
        "avg_duration_sec": round(statistics.mean(durations), 3) if durations else 0.0,
        "max_duration_sec": round(max(durations), 3) if durations else 0.0,
        "by_source": by_source,
        "by_category": by_category,
    }


def write_report(payload: dict[str, Any], report_path: Path) -> None:
    summary = payload["summary"]
    lines = [
        "# ALL REPORT",
        "",
        f"Created at: `{payload['created_at']}`",
        f"Result JSON: `{payload['result_path']}`",
        "",
        "## Summary",
        "",
        f"- Total samples: `{summary['sample_count']}`",
        f"- Pass: `{summary['pass']}`",
        f"- Partial: `{summary['partial']}`",
        f"- Fail: `{summary['fail']}`",
        f"- Avg duration: `{summary['avg_duration_sec']}s`",
        f"- Max duration: `{summary['max_duration_sec']}s`",
        "",
        "## By Source",
        "",
        "| Source | Total | Pass | Partial | Fail |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]
    for source, stat in summary["by_source"].items():
        lines.append(
            f"| {source} | {stat['total']} | {stat['pass']} | "
            f"{stat['partial']} | {stat['fail']} |"
        )
    lines.extend(
        [
            "",
            "## By Category",
            "",
            "| Category | Total | Pass | Partial | Fail |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    for category, stat in summary["by_category"].items():
        safe_category = category.replace("|", "\\|")
        lines.append(
            f"| {safe_category} | {stat['total']} | {stat['pass']} | "
            f"{stat['partial']} | {stat['fail']} |"
        )
    lines.extend(["", "## Failed Or Partial Examples", ""])
    examples = [r for r in payload["results"] if r["verdict"] != "pass"][:30]
    for item in examples:
        lines.extend(
            [
                f"### {item['index']}. {item['verdict'].upper()}",
                "",
                f"- Category: `{item['category_name']}`",
                f"- Question: {item['question']}",
                f"- Expected: {item['expected']}",
                f"- Actual: {item['actual']}",
                "",
            ]
        )
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run mixed QA eval and create ALL_REPORT.md")
    parser.add_argument("--per-category", type=int, default=10)
    parser.add_argument("--event-samples", type=int, default=20)
    parser.add_argument("--seed", type=int, default=20260423)
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rows = load_question_bank_sample(args.per_category, rng)
    rows.extend(load_event_flow_questions(args.event_samples, rng))
    rng.shuffle(rows)

    existing = load_existing_results()
    results = run_eval(
        rows,
        existing,
        per_category=args.per_category,
        event_samples=args.event_samples,
        seed=args.seed,
    )
    result_path = SUMMARY_PATH
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "seed": args.seed,
        "per_category": args.per_category,
        "event_samples": args.event_samples,
        "summary": summarize(results),
        "results": results,
    }
    payload["result_path"] = str(result_path)
    persist_summary(payload)
    write_report(payload, PROJECT_ROOT / "ALL_REPORT.md")
    print(f"RESULT={result_path}")
    print(f"REPORT={PROJECT_ROOT / 'ALL_REPORT.md'}")


if __name__ == "__main__":
    main()
