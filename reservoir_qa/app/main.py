from __future__ import annotations

import argparse
import sys


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Reservoir QA local runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("parse-pdf", help="Extract PDF text and build structured JSON")
    subparsers.add_parser("apply-schema", help="Apply SQL schema and readonly-user scripts")
    subparsers.add_parser("load-mysql", help="Load parsed JSON into MySQL")
    subparsers.add_parser("load-knowledge", help="Load parsed docs into LanceDB")

    ask_parser = subparsers.add_parser("ask", help="Route a question to SQL or RAG")
    ask_parser.add_argument("question", help="Question in Chinese")

    args = parser.parse_args()

    if args.command == "parse-pdf":
        from app.etl.tankeng_pdf_parser import export_parsed_artifacts

        path = export_parsed_artifacts()
        print(f"Parsed artifacts written to: {path}")
    elif args.command == "apply-schema":
        from app.etl.apply_schema import apply_default_schema

        apply_default_schema()
        print("Schema applied.")
    elif args.command == "load-mysql":
        from app.etl.load_mysql import load_mysql_from_parsed_json

        load_mysql_from_parsed_json()
        print("MySQL load complete.")
    elif args.command == "load-knowledge":
        from app.rag.knowledge_loader import load_knowledge

        load_knowledge()
        print("Knowledge load complete.")
    elif args.command == "ask":
        from app.agents.router import ask

        print(ask(args.question))


if __name__ == "__main__":
    main()
