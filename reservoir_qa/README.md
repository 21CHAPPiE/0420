# Reservoir QA

本项目把 `浙江省瓯江滩坑水电站2025年度水库控制运用计划.pdf` 转成：

1. 可入 MySQL 的结构化业务数据
2. 可用于 Agno Text-to-SQL 的只读查询系统
3. 可用于 Agno RAG 的本地知识库

## 目录

```text
reservoir_qa/
  app/
    agents/         Agno agents and routing
    core/           config, DB helpers, SQL guard
    etl/            PDF extraction, parsing, MySQL loading
    rag/            knowledge loading helpers
    sql/            structured metadata builders
  data/
    raw/            source PDF
    parsed/         extracted txt/json/knowledge markdown
  sql/
    001_schema.sql
  tests/
```

## 快速开始

1. 创建环境

```powershell
cd D:\a_hydro\0420\reservoir_qa
uv venv
uv sync
```

2. 配置环境变量

复制 `.env.example` 为 `.env`，至少填写：

- `DEEPSEEK_API_KEY`
- `DATABASE_URL_ADMIN`
- `DATABASE_URL_QUERY`

当前仓库已经补了一份默认 `.env`，默认值如下：

```env
LLM_PROVIDER=deepseek
DEEPSEEK_BASE_URL=https://api.deepseek.com
AGNO_MODEL_ID=deepseek-chat
EMBEDDING_PROVIDER=sentence-transformer
AGNO_EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
DATABASE_URL_ADMIN=mysql+pymysql://root:password@127.0.0.1:3306/tk_reservoir_ops
DATABASE_URL_QUERY=mysql+pymysql://app_query_ro:password@127.0.0.1:3306/tk_reservoir_ops
LANCEDB_URI=./data/lancedb
RAG_TABLE_NAME=tankeng_rag
SQL_SEMANTICS_TABLE_NAME=tankeng_sql_semantics
```

说明：

1. 这些值适用于本地开发默认约定。
2. 当前默认生成模型已切换为 DeepSeek OpenAI 兼容接口。
3. 当前 RAG embedding 默认切换为本地 `sentence-transformer`，不再依赖 OpenAI embeddings。
4. 如果你显式切回 `LLM_PROVIDER=openai`，项目仍支持从 [anth.json](./app/rag/anth.json) 回退读取 `tokens.access_token`

3. 解析 PDF

```powershell
uv run python -m app.main parse-pdf
```

4. 初始化数据库

先执行 [001_schema.sql](./sql/001_schema.sql)，再导入：

```powershell
uv run python -m app.main load-mysql
```

5. 构建知识库

```powershell
uv run python -m app.main load-knowledge
```

6. 提问

```powershell
uv run python -m app.main ask "2025年6月计划来水量是多少？"
uv run python -m app.main ask "为什么台汛期限制水位更低？"
```

## 运行模式

### 问数

走 `ReadOnlySQLTools + Agno Agent`：

1. 只暴露白名单表
2. 只允许 `SELECT / WITH`
3. 自动拒绝写操作和多语句

### 问答

走 `Knowledge + LanceDB + Agno Agent`：

1. 载入 PDF 转文本后的全文
2. 载入额外的结构化语义文档
3. 面向规则解释、预案、背景说明类问题

### 混合路由

`app.main ask` 会先做简单意图识别：

1. 数值/统计/阈值/月份 -> Text-to-SQL
2. 原因/依据/条文/说明 -> RAG
3. 模糊问题默认走 RAG

## 当前状态

目前已经完成：

1. `uv` 环境创建与依赖同步
2. PDF -> 文本 -> JSON 结构化抽取
3. MySQL 建表 SQL
4. 只读 SQL Guard
5. Agno Text-to-SQL agent 骨架
6. Agno RAG agent 骨架

当前仍依赖外部环境的部分：

1. 本机需要一个真实可连接的 MySQL 服务
2. 生成模型需要一个真正可稳定调用 DeepSeek API 的 key

## 当前实测结果

截至当前工作区状态，下面这些已经实测通过：

1. `uv sync`
2. `uv run python -m app.main parse-pdf`
3. `uv run python -m app.main apply-schema`
4. `uv run python -m app.main load-mysql`

当前 MySQL 已落地成功，示例数据包括：

1. `reservoir_basic_info = 1`
2. `reservoir_control_index = 13`
3. `reservoir_monthly_operation_plan = 12`
4. `reservoir_warning_rule = 2`
5. `reservoir_annual_operation_stat = 17`

因此，当前状态下：

1. PDF -> JSON -> MySQL 链路已打通
2. Agno agent 代码骨架已打通
3. 只要填入可用 `DEEPSEEK_API_KEY`，生成模型即可切到 DeepSeek
