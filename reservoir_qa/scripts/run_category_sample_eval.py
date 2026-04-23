from __future__ import annotations

import argparse
import difflib
import json
import statistics
import sys
import time
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

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


RESULTS_DIR = PROJECT_ROOT / "data" / "eval"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)


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
    tokens = re_find_numbers(normalize(text))
    normalized_tokens: set[str] = set()
    for token in tokens:
        try:
            normalized_tokens.add(format(Decimal(token).normalize(), "f"))
        except InvalidOperation:
            normalized_tokens.add(token)
    return normalized_tokens


def re_find_numbers(text: str) -> list[str]:
    import re

    return re.findall(r"\d+(?:\.\d+)?", text)


def reference_chunks(text: str) -> list[str]:
    import re

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

    return verdict, {
        "ratio": round(ratio, 3),
        "numbers_hit": numbers_hit,
        "chunk_hit_count": chunk_hit_count,
        "chunk_total": len(chunks),
        "chunk_hit_ratio": round(chunk_hit_ratio, 3),
    }


def load_question_set() -> tuple[Path, dict[str, Any]]:
    question_path = next(path for path in PROJECT_ROOT.glob("*.json") if path.name != "test_runs.json")
    data = json.loads(question_path.read_text(encoding="utf-8-sig"))
    return question_path, data


def build_sample_rows(data: dict[str, Any], sample_size: int) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    index = 0
    for top_name, categories in data.items():
        for category_name, qa_list in categories.items():
            for item in list(qa_list)[:sample_size]:
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Run per-category sample evaluation")
    parser.add_argument("--sample-size", type=int, default=5)
    parser.add_argument("--output-name", default="category_sample_eval_5.json")
    args = parser.parse_args()

    question_path, data = load_question_set()
    rows = build_sample_rows(data, args.sample_size)
    results: list[dict[str, Any]] = []

    for row in rows:
        build_rag_agent.cache_clear()
        build_text_to_sql_agent.cache_clear()

        started = time.perf_counter()
        exception_message: str | None = None
        try:
            actual = ask(row["question"])
            verdict, metrics = classify(row["expected"], actual)
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
            **row,
            "actual": actual,
            "verdict": verdict,
            "metrics": metrics,
            "duration_sec": duration,
            "finished_at": datetime.now().isoformat(timespec="seconds"),
        }
        if exception_message is not None:
            record["exception"] = exception_message
        results.append(record)
        print(
            f"[{row['index']}/{len(rows)}] {row['category_name']} | "
            f"{verdict} | {duration}s"
        )

    by_category: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass": 0, "partial": 0, "fail": 0, "total": 0}
    )
    by_top: dict[str, dict[str, int]] = defaultdict(
        lambda: {"pass": 0, "partial": 0, "fail": 0, "total": 0}
    )
    durations = []
    for result in results:
        category_key = f"{result['top_name']} / {result['category_name']}"
        by_category[category_key]["total"] += 1
        by_category[category_key][result["verdict"]] += 1
        by_top[result["top_name"]]["total"] += 1
        by_top[result["top_name"]][result["verdict"]] += 1
        durations.append(result["duration_sec"])

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "question_set_path": str(question_path),
        "sample_size_per_category": args.sample_size,
        "sample_count": len(results),
        "pass": sum(item["pass"] for item in by_category.values()),
        "partial": sum(item["partial"] for item in by_category.values()),
        "fail": sum(item["fail"] for item in by_category.values()),
        "avg_duration_sec": round(statistics.mean(durations), 3) if durations else 0.0,
        "max_duration_sec": round(max(durations), 3) if durations else 0.0,
        "by_top": by_top,
        "by_category": by_category,
        "results": results,
    }

    output_path = RESULTS_DIR / args.output_name
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OUTPUT={output_path}")


if __name__ == "__main__":
    main()
