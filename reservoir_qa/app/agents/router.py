from __future__ import annotations

from dataclasses import dataclass

from app.agents.rag_agent import build_rag_agent
from app.agents.text_to_sql_agent import build_text_to_sql_agent


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


def ask(question: str) -> str:
    decision = classify_question(question)
    if decision.route == "sql":
        response = build_text_to_sql_agent().run(question)
    else:
        response = build_rag_agent().run(question)
    return response.content if hasattr(response, "content") else str(response)

