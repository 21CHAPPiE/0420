from __future__ import annotations

from functools import lru_cache

from agno.agent import Agent

from app.agents.common import build_openai_model
from app.agents.structured_output import OUTPUT_SCHEMA, build_common_output_instructions
from app.rag.knowledge_loader import build_rag_knowledge


@lru_cache(maxsize=1)
def build_rag_agent() -> Agent:
    return Agent(
        model=build_openai_model(),
        knowledge=build_rag_knowledge(),
        search_knowledge=True,
        markdown=False,
        output_schema=OUTPUT_SCHEMA,
        instructions=[
            "你是水库文档问答助手，回答时以检索到的文档内容为依据。",
            "优先回答条文解释、背景原因、预案、说明类问题。",
            "若知识库依据不足，要明确说明，而不是编造。",
            "回答用中文，并尽量指出依据来自哪一类文档内容。",
            "不要输出你的思考过程、检索步骤、工具调用过程或诸如“让我先搜索”的中间话术。",
            "只输出最终答案。",
        ]
        + build_common_output_instructions("rag"),
    )
