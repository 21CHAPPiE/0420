from __future__ import annotations

from dataclasses import dataclass
from time import sleep

from app.agents.answer_schema import build_answer_json, serialize_agent_content
from app.agents.local_structured_answer import get_local_structured_answer
from app.agents.rag_agent import build_rag_agent
from app.agents.text_to_sql_agent import build_text_to_sql_agent
from app.core.db import can_connect_query_database


SQL_KEYWORDS = [
    "多少",
    "几月",
    "发电量",
    "来水量",
    "月末水位",
    "月初水位",
    "限制水位",
    "最高水位",
    "电话号码",
    "联系电话",
    "顺序",
    "统计",
    "排名",
    "最大",
    "最小",
]

RAG_KEYWORDS = [
    "为什么",
    "依据",
    "说明",
    "原理",
    "原因",
    "预案",
    "如何",
    "条文",
    "背景",
    "影响",
]


@dataclass
class RouteDecision:
    route: str
    reason: str


def classify_question(question: str) -> RouteDecision:
    if any(keyword in question for keyword in SQL_KEYWORDS):
        return RouteDecision(route="sql", reason="matched_sql_keyword")
    if any(keyword in question for keyword in RAG_KEYWORDS):
        return RouteDecision(route="rag", reason="matched_rag_keyword")
    return RouteDecision(route="rag", reason="default_rag")


def _run_with_retry(route: str, question: str):
    runner = build_text_to_sql_agent if route == "sql" else build_rag_agent
    try:
        return runner().run(question)
    except OSError:
        # NVIDIA-backed calls have intermittently raised OSError(22) during
        # longer batches. Clear cached agents once and retry the request.
        build_text_to_sql_agent.cache_clear()
        build_rag_agent.cache_clear()
        sleep(0.2)
        return runner().run(question)


def ask(question: str) -> str:
    local_answer = get_local_structured_answer(question)
    if local_answer is not None:
        return build_answer_json(
            answer=local_answer,
            route="local",
            basis="来自本地解析后的结构化 JSON 数据",
        )

    decision = classify_question(question)
    if decision.route == "sql":
        if not can_connect_query_database():
            return build_answer_json(
                answer="当前无法连接结构化数据库，不能可靠回答这类数值或统计问题。",
                route="sql",
                basis="结构化数据库连接不可用",
                code=1,
                message="query_failed",
            )
        response = _run_with_retry(route="sql", question=question)
        return serialize_agent_content(
            response.content if hasattr(response, "content") else response,
            fallback_route="sql",
        )
    else:
        response = _run_with_retry(route="rag", question=question)
        return serialize_agent_content(
            response.content if hasattr(response, "content") else response,
            fallback_route="rag",
        )
