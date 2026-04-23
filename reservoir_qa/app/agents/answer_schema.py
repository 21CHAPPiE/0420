from __future__ import annotations

import json
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel, Field


class AnswerData(BaseModel):
    answer: str = Field(description="最终给用户的答案内容，只包含结论本身")
    route: Literal["local", "sql", "rag"] = Field(description="答案来源链路")
    basis: str = Field(description="简要依据说明，不展开长篇推理")


class AnswerEnvelope(BaseModel):
    code: Literal[0, 1] = Field(description="0 表示成功，1 表示失败或依据不足")
    message: str = Field(description="本次回答状态说明")
    data: AnswerData = Field(description="核心回答数据")
    trace_id: str = Field(description="本次回答的追踪 ID")


def build_answer_json(
    *,
    answer: str,
    route: Literal["local", "sql", "rag"],
    basis: str,
    code: Literal[0, 1] = 0,
    message: str = "ok",
    trace_id: str | None = None,
) -> str:
    payload = AnswerEnvelope(
        code=code,
        message=message,
        data=AnswerData(answer=answer, route=route, basis=basis),
        trace_id=trace_id or f"qa-{route}-{uuid4().hex[:12]}",
    )
    return json.dumps(payload.model_dump(), ensure_ascii=False)


def serialize_agent_content(content: Any, fallback_route: Literal["sql", "rag"]) -> str:
    if isinstance(content, AnswerEnvelope):
        return json.dumps(content.model_dump(), ensure_ascii=False)
    if isinstance(content, BaseModel):
        try:
            return json.dumps(content.model_dump(), ensure_ascii=False)
        except Exception:
            pass
    return build_answer_json(
        answer=str(content),
        route=fallback_route,
        basis="模型未返回结构化对象，已降级为文本输出",
    )
