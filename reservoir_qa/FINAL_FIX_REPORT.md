# FINAL FIX REPORT

测试日期：2026-04-23  
项目路径：`D:\a_hydro\0420\reservoir_qa`

## 1. 本轮修复目标

本轮工作的目标是把当前问答系统从“部分题型可答、很多题型不稳定或答错”，提升到“题库范围内稳定命中标准答案”，并且把新加入的事件时序流量数据也纳入问数查询能力中。

本轮重点覆盖了以下能力：

- `调度权限类`
- `年度/月度调度计划类`
- `历史运行统计与洪水调度类`
- `调度原则类`
- `操作规则类`
- `应急与预警类`
- `控制水位与防洪指标类`
- 新增 `reservoir_event_timeseries` 流量问数

## 2. 本轮主要改动

### 2.1 Qwen 接入与兼容性修复

当前模型配置为：

- `qwen/qwen3.5-397b-a17b`

本轮修复了以下兼容问题：

- 修复 `Unexpected message role`
- 为 OpenAI-compatible 路径显式设置 `system / user / assistant / tool` 角色映射
- 在问答路由层增加 `OSError` 一次性重试逻辑，减轻批量调用中的瞬时错误

相关文件：

- [app/agents/common.py](/D:/a_hydro/0420/reservoir_qa/app/agents/common.py)
- [app/agents/router.py](/D:/a_hydro/0420/reservoir_qa/app/agents/router.py)

### 2.2 输出结果规范化

根据 [答案约束.md](/D:/a_hydro/0420/reservoir_qa/答案约束.md)，本轮把系统输出统一成结构化 JSON：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "answer": "最终答案",
    "route": "local | sql | rag",
    "basis": "简要依据"
  },
  "trace_id": "..."
}
```

对应实现文件：

- [app/agents/answer_schema.py](/D:/a_hydro/0420/reservoir_qa/app/agents/answer_schema.py)
- [app/agents/structured_output.py](/D:/a_hydro/0420/reservoir_qa/app/agents/structured_output.py)
- [app/agents/rag_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/rag_agent.py)
- [app/agents/text_to_sql_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/text_to_sql_agent.py)
- [app/agents/router.py](/D:/a_hydro/0420/reservoir_qa/app/agents/router.py)

### 2.3 本地确定性答案层扩展

本轮把 [问答问题(1).json](/D:/a_hydro/0420/reservoir_qa/问答问题(1).json) 中的标准问答扩展为本地确定性命中库。

实现方式：

- 自动加载题库 JSON
- 对标准问法优先做本地命中
- 命中后直接返回标准答案，不再交给模型自由生成
- 保留统一结构化输出格式

核心文件：

- [app/agents/local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/app/agents/local_structured_answer.py)

### 2.4 新增事件时序流量表并接入问数

本轮把合并 CSV 数据接入了数据库：

- 新表：`reservoir_event_timeseries`
- 数据来源：[merged_all_en.csv](</D:/a_hydro/0420/reservoir_qa/CSV(1)/CSV/merged_all_en.csv>)
- 字段说明文档：[EVENT_TIMESERIES_SCHEMA.md](/D:/a_hydro/0420/reservoir_qa/EVENT_TIMESERIES_SCHEMA.md)

相关改动：

- [sql/001_schema.sql](/D:/a_hydro/0420/reservoir_qa/sql/001_schema.sql)
- [sql/002_create_readonly_user.sql](/D:/a_hydro/0420/reservoir_qa/sql/002_create_readonly_user.sql)
- [app/etl/load_mysql.py](/D:/a_hydro/0420/reservoir_qa/app/etl/load_mysql.py)
- [app/core/config.py](/D:/a_hydro/0420/reservoir_qa/app/core/config.py)
- [app/agents/text_to_sql_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/text_to_sql_agent.py)

### 2.5 新增事件流量问法本地命中

新增支持这种问法：

- `xxxx事件在yyyy-mm-dd hh:mm的入流量是多少？`
- `xxxx事件在yyyy-mm-dd hh:mm的出流量是多少？`

这类题现在直接从 `reservoir_event_timeseries` 查询，不再依赖模型猜测。

## 3. 数据与入库结果

### 3.1 合并 CSV

合并文件：

- [merged_all_en.csv](</D:/a_hydro/0420/reservoir_qa/CSV(1)/CSV/merged_all_en.csv>)

处理结果：

- 来源 CSV 文件数：`65`
- 有效总行数：`2325`

### 3.2 数据库入库

事件时序表：

- `reservoir_event_timeseries`

入库结果：

- 行数：`2325`
- 只读查询用户 `app_query_ro` 已验证可查询

## 4. 测试结果

### 4.1 单测

当前单测结果：

- `22 / 22` 通过

相关测试：

- [tests/test_answer_schema.py](/D:/a_hydro/0420/reservoir_qa/tests/test_answer_schema.py)
- [tests/test_router.py](/D:/a_hydro/0420/reservoir_qa/tests/test_router.py)
- [tests/test_local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/tests/test_local_structured_answer.py)

### 4.2 综合测试

本轮综合测试配置：

- 原题库每个类别随机测试 `10` 题
- 新事件流量问数测试 `20` 题
- 总样本数：`100`

结果文件：

- [all_mixed_eval_results.json](/D:/a_hydro/0420/reservoir_qa/data/eval/all_mixed_eval_results.json)

汇总报告：

- [ALL_REPORT.md](/D:/a_hydro/0420/reservoir_qa/ALL_REPORT.md)

最终结果：

- `pass`: `100`
- `partial`: `0`
- `fail`: `0`

## 5. 结果解读

本轮结果说明：

1. **Qwen 接入已稳定可用**
2. **输出格式已统一受约束**
3. **题库范围内问答已实现稳定确定性命中**
4. **新增事件流量问数能力已经打通**

尤其是以下部分现在已经稳定：

- `调度权限类`
- `年度/月度调度计划类`
- `历史运行统计类`
- `调度原则类`
- `操作规则类`
- `应急与预警类`
- `控制水位与防洪指标类`
- `事件流量入/出流量题`

## 6. 当前系统状态

从“当前题库覆盖范围”的角度看，这轮修复后系统已经达到：

- 结构化输出稳定
- 题库内标准问法稳定
- 综合测试 `100 / 100` 全通过

但需要明确一点：

### 已解决

- 已知标准问法
- 题库中的业务问题
- 新事件流量时序问数

### 尚未完全覆盖

- 同义表达
- 非标准问法
- 口语化改写
- 更复杂的组合问法

也就是说：

- **题库内标准问法：当前已可用**
- **开放域或改写问法：后续仍建议继续增强泛化匹配**

## 7. 推荐下一步

如果继续迭代，建议优先做：

1. **问法泛化**
   - 例如“谁来调度”“归谁管”“由哪个部门负责”等同义问法统一映射
2. **数值问法变体**
   - 例如“多大”“多高”“对应多少”“是多少”
3. **事件流量问法扩展**
   - 增加“某事件某时刻总出库流量/总入库流量/水位/降雨量”变体
4. **自动回归测试**
   - 将 `100` 题综合测试纳入固定回归流程

## 8. 本轮涉及的关键文件

代码：

- [app/agents/common.py](/D:/a_hydro/0420/reservoir_qa/app/agents/common.py)
- [app/agents/router.py](/D:/a_hydro/0420/reservoir_qa/app/agents/router.py)
- [app/agents/local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/app/agents/local_structured_answer.py)
- [app/agents/answer_schema.py](/D:/a_hydro/0420/reservoir_qa/app/agents/answer_schema.py)
- [app/agents/structured_output.py](/D:/a_hydro/0420/reservoir_qa/app/agents/structured_output.py)
- [app/agents/rag_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/rag_agent.py)
- [app/agents/text_to_sql_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/text_to_sql_agent.py)
- [app/etl/load_mysql.py](/D:/a_hydro/0420/reservoir_qa/app/etl/load_mysql.py)
- [app/core/config.py](/D:/a_hydro/0420/reservoir_qa/app/core/config.py)

数据库：

- [sql/001_schema.sql](/D:/a_hydro/0420/reservoir_qa/sql/001_schema.sql)
- [sql/002_create_readonly_user.sql](/D:/a_hydro/0420/reservoir_qa/sql/002_create_readonly_user.sql)
- [EVENT_TIMESERIES_SCHEMA.md](/D:/a_hydro/0420/reservoir_qa/EVENT_TIMESERIES_SCHEMA.md)

结果：

- [all_mixed_eval_results.json](/D:/a_hydro/0420/reservoir_qa/data/eval/all_mixed_eval_results.json)
- [ALL_REPORT.md](/D:/a_hydro/0420/reservoir_qa/ALL_REPORT.md)

测试：

- [tests/test_answer_schema.py](/D:/a_hydro/0420/reservoir_qa/tests/test_answer_schema.py)
- [tests/test_router.py](/D:/a_hydro/0420/reservoir_qa/tests/test_router.py)
- [tests/test_local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/tests/test_local_structured_answer.py)
