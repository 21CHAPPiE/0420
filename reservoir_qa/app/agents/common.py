from __future__ import annotations

from agno.models.openai import OpenAIChat

from app.core.config import get_config


def build_openai_model() -> OpenAIChat:
    config = get_config()
    if config.llm_provider.lower() == "deepseek":
        return OpenAIChat(
            id=config.model_id,
            api_key=config.deepseek_api_key,
            base_url=config.deepseek_base_url,
            role_map={
                "system": "system",
                "user": "user",
                "assistant": "assistant",
                "tool": "tool",
                "model": "assistant",
            },
        )
    return OpenAIChat(
        id=config.model_id,
        api_key=config.openai_api_key,
        base_url=config.openai_base_url,
        role_map={
            "system": "system",
            "user": "user",
            "assistant": "assistant",
            "tool": "tool",
            "model": "assistant",
        },
    )
