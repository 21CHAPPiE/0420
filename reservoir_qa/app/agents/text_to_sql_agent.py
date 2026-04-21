from __future__ import annotations

from agno.agent import Agent

from app.agents.common import build_openai_model
from app.core.config import get_config
from app.core.sql_guard import ReadOnlySQLTools
from app.rag.knowledge_loader import build_sql_semantics_knowledge


ALLOWED_TABLES = [
    "reservoir_basic_info",
    "reservoir_control_index",
    "reservoir_period_rule",
    "reservoir_dispatch_rule",
    "reservoir_dispatch_authority_rule",
    "reservoir_monthly_operation_plan",
    "reservoir_warning_rule",
    "spillway_gate_operation_rule",
    "reservoir_annual_operation_stat",
    "reservoir_gate_operation_log",
    "reservoir_flood_forecast_stat",
    "reservoir_contact_directory",
    "reservoir_engineering_characteristic",
]


def build_text_to_sql_agent() -> Agent:
    config = get_config()
    sql_tools = ReadOnlySQLTools(
        db_url=config.database_url_query,
        allowed_tables=ALLOWED_TABLES,
        default_limit=50,
    )
    return Agent(
        model=build_openai_model(),
        tools=[sql_tools],
        knowledge=build_sql_semantics_knowledge(),
        search_knowledge=True,
        markdown=True,
        instructions=[
            "你是水库问数助手，只能回答结构化数据库中可查询的问题。",
            "在生成 SQL 前，先用 list_tables / describe_table 理解表结构。",
            "优先参考知识库中的中文字段语义映射，避免误用单位。",
            "本项目中所有 *_100m_m3 字段统一表示 亿m3，绝不能解释成100万立方米。",
            "只使用白名单表，不要推测不存在的表或字段。",
            "当问题无法通过结构化数据回答时，明确说明应改走文档问答链路。",
            "结果回答用中文，结论先行，必要时给出简短表格摘要。",
            "不要输出你的思考过程、检索步骤、工具调用过程或诸如“让我先查看”的中间话术。",
            "只输出对用户有用的最终答案。",
        ],
    )
