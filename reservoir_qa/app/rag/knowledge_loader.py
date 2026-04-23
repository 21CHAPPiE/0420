from __future__ import annotations

from pathlib import Path

from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.embedder.sentence_transformer import SentenceTransformerEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb, SearchType

from app.core.config import get_config

RAG_MAX_RESULTS = 3
SQL_SEMANTICS_MAX_RESULTS = 2


def build_embedder():
    config = get_config()
    provider = config.embedding_provider.lower()
    if provider == "sentence-transformer":
        return SentenceTransformerEmbedder(id=config.embedding_model_id)
    return OpenAIEmbedder(
        id=config.embedding_model_id,
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
    )


def build_rag_knowledge() -> Knowledge:
    config = get_config()
    return Knowledge(
        max_results=RAG_MAX_RESULTS,
        vector_db=LanceDb(
            uri=config.lancedb_uri,
            table_name=config.rag_table_name,
            search_type=SearchType.vector,
            embedder=build_embedder(),
        ),
    )


def build_sql_semantics_knowledge() -> Knowledge:
    config = get_config()
    return Knowledge(
        max_results=SQL_SEMANTICS_MAX_RESULTS,
        vector_db=LanceDb(
            uri=config.lancedb_uri,
            table_name=config.sql_semantics_table_name,
            search_type=SearchType.vector,
            embedder=build_embedder(),
        ),
    )


def load_knowledge(recreate: bool = True) -> None:
    config = get_config()
    rag_knowledge = build_rag_knowledge()
    sql_knowledge = build_sql_semantics_knowledge()

    if recreate:
        if rag_knowledge.vector_db is not None:
            rag_knowledge.vector_db.drop()
            rag_knowledge.vector_db.create()
        if sql_knowledge.vector_db is not None:
            sql_knowledge.vector_db.drop()
            sql_knowledge.vector_db.create()

    if config.parsed_text_path.exists():
        rag_knowledge.insert(name="tankeng_plan_text", path=str(config.parsed_text_path), skip_if_exists=True)

    if config.rag_docs_dir.exists():
        for path in sorted(config.rag_docs_dir.glob("*.txt")):
            rag_knowledge.insert(name=path.stem, path=str(path), skip_if_exists=True)
            sql_knowledge.insert(name=path.stem, path=str(path), skip_if_exists=True)


if __name__ == "__main__":
    load_knowledge()
    print("Knowledge loaded.")
