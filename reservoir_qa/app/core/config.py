from __future__ import annotations

import os
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


def _load_dotenv() -> None:
    env_path = Path(__file__).resolve().parents[2] / ".env"
    if not env_path.exists():
        return
    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        normalized_value = value.strip()
        if normalized_value == "":
            continue
        os.environ.setdefault(key.strip(), normalized_value)


_load_dotenv()


def _load_openai_key_from_anth_json(project_root: Path) -> Optional[str]:
    anth_path = project_root / "app" / "rag" / "anth.json"
    if not anth_path.exists():
        return None
    try:
        payload = json.loads(anth_path.read_text(encoding="utf-8"))
        if not isinstance(payload, list) or not payload:
            return None
        first = payload[0]
        if not isinstance(first, dict):
            return None
        tokens = first.get("tokens")
        if not isinstance(tokens, dict):
            return None
        access_token = tokens.get("access_token")
        if isinstance(access_token, str) and access_token.strip():
            return access_token.strip()
    except Exception:
        return None
    return None


@dataclass(frozen=True)
class AppConfig:
    project_root: Path
    data_dir: Path
    raw_dir: Path
    parsed_dir: Path
    sql_dir: Path
    pdf_path: Path
    parsed_text_path: Path
    parsed_json_path: Path
    rag_docs_dir: Path
    lancedb_uri: str
    rag_table_name: str
    sql_semantics_table_name: str
    database_url_admin: str
    database_url_query: str
    llm_provider: str
    model_id: str
    embedding_provider: str
    embedding_model_id: str
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    deepseek_api_key: Optional[str]
    deepseek_base_url: Optional[str]
    pdftotext_path: str


def get_config() -> AppConfig:
    project_root = Path(__file__).resolve().parents[2]
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    parsed_dir = data_dir / "parsed"
    rag_docs_dir = parsed_dir / "knowledge"
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        openai_api_key = _load_openai_key_from_anth_json(project_root)
    openai_base_url = os.getenv("OPENAI_BASE_URL")
    if openai_base_url is not None:
        openai_base_url = openai_base_url.strip() or None
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
    deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    if deepseek_base_url is not None:
        deepseek_base_url = deepseek_base_url.strip() or None
    return AppConfig(
        project_root=project_root,
        data_dir=data_dir,
        raw_dir=raw_dir,
        parsed_dir=parsed_dir,
        sql_dir=project_root / "sql",
        pdf_path=raw_dir / "tankeng_2025_plan.pdf",
        parsed_text_path=parsed_dir / "tankeng_2025_plan.txt",
        parsed_json_path=parsed_dir / "tankeng_2025_plan.json",
        rag_docs_dir=rag_docs_dir,
        lancedb_uri=os.getenv("LANCEDB_URI", str(project_root / "data" / "lancedb")),
        rag_table_name=os.getenv("RAG_TABLE_NAME", "tankeng_rag"),
        sql_semantics_table_name=os.getenv("SQL_SEMANTICS_TABLE_NAME", "tankeng_sql_semantics"),
        database_url_admin=os.getenv(
            "DATABASE_URL_ADMIN",
            "mysql+pymysql://root:password@127.0.0.1:3306/tk_reservoir_ops",
        ),
        database_url_query=os.getenv(
            "DATABASE_URL_QUERY",
            "mysql+pymysql://app_query_ro:password@127.0.0.1:3306/tk_reservoir_ops",
        ),
        llm_provider=os.getenv("LLM_PROVIDER", "deepseek"),
        model_id=os.getenv("AGNO_MODEL_ID", "deepseek-chat"),
        embedding_provider=os.getenv("EMBEDDING_PROVIDER", "sentence-transformer"),
        embedding_model_id=os.getenv(
            "AGNO_EMBEDDING_MODEL",
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        ),
        openai_api_key=openai_api_key,
        openai_base_url=openai_base_url,
        deepseek_api_key=deepseek_api_key,
        deepseek_base_url=deepseek_base_url,
        pdftotext_path=os.getenv(
            "PDFTOTEXT_PATH",
            r"F:\Users\Win\AppData\Local\Programs\MiKTeX\miktex\bin\x64\pdftotext.exe",
        ),
    )
