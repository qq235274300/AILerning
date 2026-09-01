# Agent Day61-75 阶段总结

更新日期：2026-09-01

## 1. 当前阶段结论

项目已经从固定顺序的手写 Pipeline，迁移到一套可以运行的 LangGraph Agent 主流程。当前 Graph 已具备状态管理、动态路由、模型自主选择工具、ToolNode 执行、多轮工具调用、上下文整理、答案生成、Patch 建议、Reviewer 检查和节点级流式输出。

当前完成的是“单次请求内的 Agent 图”。跨请求 Memory、Patch 人工确认与恢复、Crash 子图和旧 Pipeline 下线尚未完成，正好对应 Day76-80。

检查结果：

- 使用项目 `.venv` 可以成功导入并编译当前 Graph。
- 相关 Python 文件通过 `py_compile` 静态语法检查。
- 检查过程没有调用 OpenAI API，也没有消耗 tokens。
- 当前 Graph 拓扑与预期一致，包含 `tools -> tool_model` 循环。
- 项目仍处于新旧双轨状态，暂时不能删除旧 Pipeline 文件。

## 2. 当前系统能力

### 2.1 RAG

本地知识库已经支持：

- PDF 转文本与 Document。
- Document metadata，包括 `source` 和 `page`。
- 文本切分、Embedding 和 Chroma 持久化。
- 多文档知识库，目前包含 UE 和 DirectX 资料。
- Retriever 返回文档片段、来源、页码、距离和相关性评分。
- Rerank 模块和 Top-K 检索流程；当前 Rerank 只是按 Chroma distance 重新排序的本地占位实现，尚未接入 BGE reranker 模型。

### 2.2 Agent 工具

本地只读工具：

- `read_file(path)`：读取项目文本文件。
- `list_files(directory)`：列出目录内容。
- `search_code(keyword, directory)`：搜索源码。
- `search_logs(keyword, directory)`：搜索日志。

知识工具：

- `search_ue_docs(query)`：搜索 UE / DirectX 本地知识库。
- `search_web(query)`：查询实时或公共网络信息。

这些函数通过 `@tool` 包装成 LangChain Tool，再注册到 `ToolNode`。模型通过 `bind_tools()` 获得工具说明，`ToolNode` 根据 `AIMessage.tool_calls` 真正执行 Python 工具。

### 2.3 分析与输出

- Planner 输出结构化 `RequestAnalysis`。
- Writer 输出结构化 `DraftAnswer`。
- Patcher 只生成 `PatchSuggestion`，不会修改文件。
- Reviewer 检查证据、引用、风险和 Patch 建议。
- Final 节点选择草稿或 Reviewer 修订后的最终答案。

### 2.4 API 和前端

当前保留以下入口：

| API | 实现 | 状态 |
| --- | --- | --- |
| `/chat`、`/chat/stream` | 早期 LLM/RAG 聊天 | 旧入口 |
| `/agent`、`/agent/stream` | `Agent/pipeline.py` | 旧手写 Pipeline |
| `/crash` | `Agent/crash_analyzer.py` | 独立 Crash 流程 |
| `/agent/graph` | LangGraph 同步调用 | 新入口 |
| `/agent/graph/stream` | LangGraph 节点级 NDJSON 流 | 新主入口 |

`index.html` 当前调用 `/agent/graph/stream`，可以显示节点执行路径、最终答案、Patch、Reviewer 和总耗时。它目前是节点级流式输出，不是 Writer token streaming。

## 3. 当前 Graph 结构

```text
START
  |
Planner
  |-- 普通问题 ------------------------------> Writer
  |
  `-- 需要文件、日志、RAG 或 Web ------------> Tool Model
                                                   |
                                有 tool_calls      |      无 tool_calls
                                      |            |            |
                                      v            |            v
                                    Tools ---------+      Build Context
                                                               |
                                                               v
                                                             Writer
                                                               |
                      +----------------------------------------+-------------------+
                      |                                        |                   |
                   Patcher                                  Reviewer             Final
                      |                                        |                   |
                      `--------------------> Reviewer ----------+------------------> Final
                                                                                     |
                                                                                    END
```

`tools -> tool_model` 是有意设计的循环：工具执行后，模型读取 `ToolMessage`，再决定继续调用其他工具，还是结束上下文收集。

## 4. State 中各字段的职责

`AgentState` 继承 `MessagesState`，同时保留项目自己的业务字段。

| 字段 | 作用 |
| --- | --- |
| `messages` | LangGraph 消息历史，保存 Human、AI 和 Tool 消息 |
| `user_request` | 当前轮用户问题，供现有 Planner、Writer、Patcher、Reviewer 使用 |
| `analysis` | Planner 生成的任务类型和上下文需求 |
| `context` | 工具真正找到并整理后的文件、代码、日志、文档和 Web 证据 |
| `draft` | Writer 草稿 |
| `patch_suggestion` | 只读 Patch 建议 |
| `review` | Reviewer 检查结果 |
| `final_answer` | 最终返回文本 |
| `timings` | 节点和总耗时，当前 Graph 只稳定记录总耗时 |

`analysis` 是“需要找什么”的计划，`context` 是“实际找到了什么”的证据。`build_context_node()` 将 LangGraph 的 `ToolMessage` 转换为现有 Writer、Patcher 和 Reviewer 能使用的 `CollectedContext`。

## 5. 单次请求的完整执行过程

以“分析 `day-01/Agent/graph/state.py`”为例：

1. API 调用 `create_initial_state()`，写入 `user_request` 和首条 `HumanMessage`。
2. Planner 识别为代码分析，标记需要文件上下文和 Reviewer。
3. 路由进入 `tool_model`。
4. 模型生成 `read_file` 的 `tool_calls`。
5. `tools_condition` 将 Graph 路由到 `ToolNode`。
6. `ToolNode` 执行 `read_file_tool.invoke()`，返回 `ToolMessage`。
7. Graph 回到 `tool_model`，模型检查工具结果是否足够。
8. 模型不再调用工具时，进入 `build_context`。
9. `build_context` 把文件结果放入 `context.files`。
10. Writer 根据问题、Analysis 和 Context 生成草稿。
11. 代码分析满足 Patch 条件，进入 Patcher。
12. Reviewer 检查答案与 Patch 风险。
13. Final 输出 Reviewer 的最终答案。
14. 流式 API 每完成一个节点就发送一条 NDJSON 事件。

## 6. Day76 前需要完善的事项

### 高优先级

#### 6.1 定义“当前轮”的消息边界

`build_context_node()` 当前遍历全部 `state["messages"]`。启用 Checkpointer 后，同一个 `thread_id` 会保存多轮消息，如果继续扫描全部历史，就会把上一轮 `ToolMessage` 重复加入本轮 Context。

Day77 实现 Memory 时必须只解析当前轮最后一条 `HumanMessage` 之后的 ToolMessage，或者在 State 中记录当前轮起始消息位置/轮次 ID。

#### 6.2 修正流式 API 的外部 State 合并

`service.py` 使用：

```python
current_state.update(node_update)
```

这只是 API 层对节点更新的副本汇总，不参与 LangGraph 内部运行。普通字段可以直接覆盖，但 `messages` 在 LangGraph 内部使用 `add_messages` reducer，普通 `dict.update()` 会把历史消息替换成最新一批消息。

当前最终响应不返回 `messages`，所以暂时不影响答案；Memory 阶段需要改为使用 `add_messages`、读取 Graph 最终快照，或调整流模式。

#### 6.3 增加 Tool 循环上限

同步和流式调用目前都没有显式设置 `recursion_limit`。应为 Graph 调用添加合理上限，例如 8-12，避免模型重复调用工具导致流程过长。

#### 6.4 加固文件路径检查

`resolve_safe_path()` 当前使用字符串 `startswith()` 判断路径是否位于项目根目录。更稳妥的实现应使用 Python 3.11 的 `Path.is_relative_to(PROJECT_ROOT)`，避免相同字符串前缀的相邻目录通过检查。

同时建议为 `read_file` 增加允许的文本后缀和最大读取长度，避免误读超大文件并推高上下文 tokens。

#### 6.5 固定 Chroma 持久化目录

`RAG/chroma.py` 当前使用 `PersistentClient(path="./chroma_db")`。相对路径取决于启动命令的当前工作目录，从项目根目录和 `day-01` 启动可能连接到两个不同的数据库。

应把路径固定为基于代码文件计算出的绝对路径，并在迁移前确认哪一个 `chroma_db` 是当前有效知识库，避免查询到空库或旧库。

### 中优先级

#### 6.6 增加依赖清单

仓库当前没有 `requirements.txt` 或其他依赖清单，但实际依赖已经包含：

- `fastapi`
- `uvicorn`
- `openai`
- `pydantic`
- `python-dotenv`
- `langgraph`
- `langchain-core`
- `langchain-openai`
- Chroma、PDF/OCR 相关依赖

目前必须使用 `D:\Me\VSCodeProjects\.venv` 才能导入 LangGraph；全局 Python 没有这些依赖。Day80 前应补充依赖清单，保证项目可复现。

#### 6.7 增加不消耗 OpenAI tokens 的测试

当前没有覆盖新 Graph 的自动化测试。至少需要：

- State 初始化和消息 reducer 测试。
- Planner/Writer 路由函数测试。
- ToolNode 使用假工具的测试。
- `build_context_node()` 分类 ToolMessage 的测试。
- API NDJSON 事件格式测试。
- Memory 中不同 `thread_id` 隔离测试。
- Patch interrupt/resume 测试。

测试应使用 Fake Model 或替换节点，避免真实调用 OpenAI API。

### 迁移清理项

以下代码仍被旧 `/agent` 链路使用，Day80 前不能直接删除：

- `Agent/pipeline.py`
- `Agent/collector.py`
- `Agent/searcher.py`
- `Agent/tool_runner.py`
- `Agent/tool_schemas.py`

新 Graph 已不再注册 `collector_node` 和 `searcher_node`，但 `nodes.py` 仍保留它们及旧模块导入，`routing.py` 和 `workflow.py` 仍保留未使用的 `route_after_collector`。这些属于 Day80 的确认删除候选。

仓库还跟踪了一个旧的 `day-01/__pycache__/main.cpython-39.pyc`。虽然 `.gitignore` 已忽略 `__pycache__`，已跟踪文件不会自动取消跟踪，应在后续清理提交中从 Git 索引移除。

## 7. Day76-80 建议执行顺序

### Day76：Checkpointer 与 thread_id

学习目标：理解 Graph State、Checkpointer、线程配置和普通 Python 全局变量之间的区别。

落地内容：

- 了解 `checkpointer` 保存的是 Graph 状态快照。
- 了解 `configurable.thread_id` 如何定位一段会话。
- 区分“同一轮工具消息”和“跨轮会话消息”。
- 设计新的 `AgentRequest(question, thread_id)`。
- 暂时只用最小演示图验证，不立即修改正式 API。

### Day77：短期会话 Memory

落地内容：

- 使用内存 Checkpointer 编译正式 Graph。
- API 接收并传递 `thread_id`。
- 同一 `thread_id` 追加消息，不同 `thread_id` 相互隔离。
- 每轮重置 `context`、`draft`、`patch_suggestion`、`review` 和 `final_answer`。
- `build_context_node()` 只读取当前轮 ToolMessage。
- 修正流式 API 对最终 State 和 messages 的处理。

完成标准：用户先问“分析 state.py”，再问“刚才那个类为什么继承 MessagesState”，Agent 能利用上一轮消息理解“刚才那个类”。

### Day78：Patch 人工确认与暂停恢复

落地内容：

- 在 Patcher 后增加 approval 节点。
- 使用 LangGraph interrupt 暂停 Graph。
- 前端显示 Patch、风险以及确认/拒绝按钮。
- 确认后恢复进入 Reviewer；拒绝后不应用修改并进入 Final。
- 本阶段仍不真实修改文件。

完成标准：生成 Patch 后 Graph 进入等待状态，只有带相同 `thread_id` 恢复后才继续。

### Day79：Crash Agent 子图

落地内容：

- 将读取日志、错误摘要、RAG 检索和报告生成拆成 Crash 子图。
- 主 Planner 将 `crash_analysis` 路由到子图。
- 子图完成后把结构化报告写回主 State。
- 保留 `/crash` 作为临时兼容入口，验证一致后再决定是否删除。

完成标准：普通问题不进入 Crash 子图，Crash 日志问题自动完成读取、提取、检索和报告生成。

### Day80：完全迁移与清理

落地内容：

- 将 `/agent` 和 `/agent/stream` 切换到 LangGraph Service。
- 更新前端使用正式 API 和 `thread_id`。
- 对比旧、新流程的普通问答、代码分析、RAG、Web、Crash 和 Patch 输出。
- 通过搜索确认引用后，删除旧 Pipeline 和重复工具调度代码。
- 清理未使用节点、路由、Schema、演示文件和已跟踪缓存文件。
- 增加依赖清单和最小自动化测试。
- 重新生成 Graph 图片并更新项目说明。

Day80 完成后再开始 Writer token streaming，避免同时改 Memory、恢复机制和输出协议。

## 8. Day76 开始前的完成标准

- [x] 当前 Python 文件通过静态语法检查。
- [x] 使用项目 `.venv` 可以导入并编译 Graph。
- [x] Graph 拓扑包含 Planner、Tool Calling、Context、Writer、Patcher、Reviewer 和 Final。
- [x] 新 Graph API 和前端入口已经存在。
- [ ] 为 Graph 调用增加 `recursion_limit`。
- [ ] 明确当前轮 ToolMessage 的边界方案。
- [ ] 确定 Memory API 的 `thread_id` 请求格式。
- [ ] 决定流式模式下如何取得最终真实 State。
- [ ] 补充依赖清单和无 tokens 测试计划。

结论：可以进入 Day76，但 Day76 不应直接给现有 Graph 加 Memory。先理解 Checkpointer 和 `thread_id`，并把“当前轮边界”和“最终 State 获取方式”设计清楚，再在 Day77 接入正式流程。
