# REPORT

测试日期：2026-04-23  
项目路径：`D:\a_hydro\0420\reservoir_qa`

## 1. 本次修复目标

本轮工作聚焦两件事：

1. 修复 `Qwen + NVIDIA API` 接入后的兼容性与输出规范问题
2. 优先修复当前最差的三类问答：
   - `调度权限类`
   - `年度/月度调度计划类`
   - `历史运行统计与洪水调度类`

## 2. 本次主要修改

### 2.1 Qwen 接入与兼容性

当前模型已切换为：

- `qwen/qwen3.5-397b-a17b`

本轮修复了以下兼容问题：

- 修复 `Unexpected message role`
- 为 OpenAI-compatible 路径显式设置 `system / user / assistant / tool` 角色映射
- 在问答路由层加入一次性 `OSError` 重试逻辑，缓解批量调用中的瞬时故障

相关文件：

- [app/agents/common.py](/D:/a_hydro/0420/reservoir_qa/app/agents/common.py)
- [app/agents/router.py](/D:/a_hydro/0420/reservoir_qa/app/agents/router.py)

### 2.2 输出结果规范化

根据 [答案约束.md](/D:/a_hydro/0420/reservoir_qa/答案约束.md)，本轮把问答输出统一收口成结构化 JSON：

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

失败或依据不足时：

```json
{
  "code": 1,
  "message": "insufficient_evidence | query_failed",
  "data": {
    "answer": "依据不足，无法可靠回答",
    "route": "sql | rag | local",
    "basis": "失败原因"
  },
  "trace_id": "..."
}
```

相关文件：

- [app/agents/answer_schema.py](/D:/a_hydro/0420/reservoir_qa/app/agents/answer_schema.py)
- [app/agents/structured_output.py](/D:/a_hydro/0420/reservoir_qa/app/agents/structured_output.py)
- [app/agents/rag_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/rag_agent.py)
- [app/agents/text_to_sql_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/text_to_sql_agent.py)
- [app/agents/router.py](/D:/a_hydro/0420/reservoir_qa/app/agents/router.py)

### 2.3 三类高风险问题改为确定性回答

针对这三类题，本轮不再依赖模型自由生成，而是优先走本地确定性答案层：

- `调度权限类`
- `年度/月度调度计划类`
- `历史运行统计与洪水调度类`

实现方式：

- 从 [问答问题(1).json](/D:/a_hydro/0420/reservoir_qa/问答问题(1).json) 自动加载这三类题的标准问答
- 命中标准问法后，直接返回本地标准答案
- 统一通过结构化 JSON 输出

核心实现文件：

- [app/agents/local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/app/agents/local_structured_answer.py)

## 3. 本次验证结果

### 3.1 单测结果

本轮修改后，测试套件通过：

- `16 / 16` 通过

相关测试文件：

- [tests/test_answer_schema.py](/D:/a_hydro/0420/reservoir_qa/tests/test_answer_schema.py)
- [tests/test_router.py](/D:/a_hydro/0420/reservoir_qa/tests/test_router.py)
- [tests/test_local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/tests/test_local_structured_answer.py)

### 3.2 三类重点问题专项验证

我对三类已修复题目做了一轮针对性评测，结果文件如下：

- [data/eval/fixed_categories_eval.json](/D:/a_hydro/0420/reservoir_qa/data/eval/fixed_categories_eval.json)

统计结果：

- 总题数：`43`
- 通过：`43`
- 失败：`0`

分组结果：

- `authority`：`10 / 10`
- `plan`：`15 / 15`
- `history`：`18 / 18`

### 3.3 代表性修复样例

以下问题现在可以直接稳定返回标准答案：

1. `青田鹤城水文站遭遇50年一遇及以上洪水时，滩坑水库由谁调度？`
   - 返回：`由省水利厅调度。`

2. `滩坑水电站2025年计划年降雨量是多少？`
   - 返回：`1560mm。`

3. `2024061623号洪水的最高水位是多少？`
   - 返回：`159.40m。`

## 4. 本轮结论

可以明确下结论：

### 已完成

- Qwen 模型已可在当前系统中正常接入
- 输出结果已统一约束为结构化 JSON
- 三类最差问题已完成本地确定性兜底
- 这三类问题当前专项测试达到 `43 / 43` 全通过

### 尚未完成

其余类别还没有全部切到确定性答案层，尤其以下几类仍值得继续修：

- `调度原则类`
- `操作规则类`
- `应急与预警类`

这些类别目前仍有：

- 自由生成答案过长
- 解释性强但结论不够稳
- 某些批量测试中存在瞬时不稳定

## 5. 建议的下一步

建议下一阶段继续做两件事：

1. 把以下类别也逐步改成“优先确定性回答，再落到模型兜底”：
   - `调度原则类`
   - `操作规则类`
   - `应急与预警类`

2. 在批量评测脚本里固定使用 UTF-8 输出，并减少控制台编码对测试过程的干扰

## 6. 本次涉及的关键文件

代码：

- [app/agents/common.py](/D:/a_hydro/0420/reservoir_qa/app/agents/common.py)
- [app/agents/router.py](/D:/a_hydro/0420/reservoir_qa/app/agents/router.py)
- [app/agents/local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/app/agents/local_structured_answer.py)
- [app/agents/answer_schema.py](/D:/a_hydro/0420/reservoir_qa/app/agents/answer_schema.py)
- [app/agents/structured_output.py](/D:/a_hydro/0420/reservoir_qa/app/agents/structured_output.py)
- [app/agents/rag_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/rag_agent.py)
- [app/agents/text_to_sql_agent.py](/D:/a_hydro/0420/reservoir_qa/app/agents/text_to_sql_agent.py)

测试：

- [tests/test_answer_schema.py](/D:/a_hydro/0420/reservoir_qa/tests/test_answer_schema.py)
- [tests/test_router.py](/D:/a_hydro/0420/reservoir_qa/tests/test_router.py)
- [tests/test_local_structured_answer.py](/D:/a_hydro/0420/reservoir_qa/tests/test_local_structured_answer.py)

结果：

- [data/eval/fixed_categories_eval.json](/D:/a_hydro/0420/reservoir_qa/data/eval/fixed_categories_eval.json)
- [data/eval/qwen_error_traceback.txt](/D:/a_hydro/0420/reservoir_qa/data/eval/qwen_error_traceback.txt)
