from __future__ import annotations

from typing import Literal

from app.agents.answer_schema import AnswerEnvelope


def build_common_output_instructions(route: Literal["sql", "rag"]) -> list[str]:
    route_basis = {
        "sql": "依据应简要描述查询到的表或字段，不要编造不存在的表字段。",
        "rag": "依据应简要描述命中的文档类型或知识条目，不要编造来源。",
    }[route]
    return [
        "严格按给定 output_schema 返回，不要输出 schema 之外的额外文本。",
        "data.answer 只写最终答案本身，避免长篇过程解释。",
        "message 只允许写简短状态，例如 ok、insufficient_evidence、query_failed。",
        route_basis,
        "如果依据不足，不要编造；code 设为 1，message 设为 insufficient_evidence，data.answer 明确写“依据不足，无法可靠回答”。",
    ]


OUTPUT_SCHEMA = AnswerEnvelope
