# Day80：正式切换 LangGraph

## 正式入口

- `POST /agent`：同步返回；请求为 `{"question":"...","thread_id":"session-1"}`。
- `POST /agent/stream`：相同请求，返回节点级 NDJSON 事件，并非逐 token 输出。
- `POST /agent/resume`：请求为 `{"thread_id":"session-1","decision":"approve","feedback":""}`，也支持 `reject`。
- `/agent/graph`、`/agent/graph/stream`、`/agent/graph/resume` 保留为 deprecated 兼容别名，使用同一个实现。
- `POST /crash`：请求为 `{"path":"day-01/TestLogs/crash.log"}`，直接运行同一个 Crash 子图，不经过 Planner，也不保存聊天历史。
- `/chat`、`/chat/stream` 保留为独立的早期聊天学习接口，不是正式 Agent 入口。

旧 `/agent` 调用者必须增加 `thread_id`，否则返回 422；旧 Pipeline 的阶段事件已替换为图节点事件。前端已切换到正式 URL。

## 唯一 Agent 主流程

```text
Planner
  ├─ 普通问题 → Writer
  ├─ 需要上下文 → tool_model ↔ tools → build_context → Writer
  └─ Crash → Crash 子图 → Final
Writer → 按需 Patcher → 人工确认 → Reviewer → Final
```

普通 Writer 任务也可能直接进入 Reviewer 或 Final。拒绝 Patch 后直接 Final，不写文件。

## 清理范围

删除旧 `Agent/pipeline.py`、`collector.py`、`searcher.py`、`tool_runner.py`、`tool_schemas.py`，以及闲置的 Collector/Searcher 图节点与重复模型。保留仍被图使用的 Planner、Writer、Patcher、Reviewer、工具实现与 RAG。Crash 模块保留提取摘要和生成报告函数，删除旧顺序调度。

## 回归测试

在 `day-01` 目录运行（不调用真实 OpenAI）：

```powershell
..\.venv\Scripts\python.exe -m unittest discover -s Test -p "test_day*.py" -v
```

测试覆盖正式 API/兼容别名、真实 ToolNode 调用、会话历史、Patch 确认/拒绝/重复恢复、Crash 子图及跨轮状态清理。

## 仍然保留的限制

- InMemorySaver 仅在当前进程保存历史，重启丢失；同一 thread_id 不应并发提交请求。
- Checkpoint 自定义 Pydantic 类型仍有反序列化兼容警告，升级前需要处理类型白名单。
- Crash 只接受一个明确的 `.log` 路径，读取日志末尾 20000 个字符。
- Patch 只是建议，接受后执行审查，不自动修改文件。
- Writer token streaming、持久化 Memory 和生产级并发控制不在 Day80 范围。
