from typing import Literal
from Agent.graph.state import AgentState

def should_collect_context(state: AgentState) -> bool:
    """
    是否需要读取项目文件、搜索代码或搜索日志。
    """
    analysis = state["analysis"]
    return (
        analysis.needs_file_context or analysis.needs_logs_context or bool(analysis.file_paths)
    )
    
def should_search_knowledge(state: AgentState) -> bool:
    """
    是否需要搜索RAG知识库或Web
    """
    analysis = state["analysis"]
    return (
        analysis.needs_rag_context or analysis.needs_web_search or
        analysis.task_type in {"crash_analysis","log_analysis"}
    )

def should_propose_patch(state: AgentState) -> bool:
    """
    是否需要生成 Patch 建议。
    """
    analysis = state["analysis"]
    return (
        analysis.needs_file_context
        and analysis.needs_review
        and analysis.task_type in {
            "code_analysis",
            "crash_analysis",
            "log_analysis"
        }
    )

def should_review_answer(state: AgentState) -> bool:
    """
    是否需要 Reviewer 检查答案。
    """
    return state["analysis"].needs_review

def route_after_planner(
    state: AgentState
) -> Literal["crash_analysis", "tool_model", "writer"]:
    """
    Planner 只做粗粒度判断。

    需要外部上下文：
        进入 Tool Calling 循环。

    普通问题：
        直接交给 Writer。
    """
    # Crash 优先进入专用子图，避免通用工具流程重复分析和生成 Patch。
    if state["analysis"].task_type == "crash_analysis":
        return "crash_analysis"
    if (
        should_collect_context(state)
        or should_search_knowledge(state)
    ):
        return "tool_model"

    return "writer"

def route_after_writer(state: AgentState) -> Literal["patcher","reviewer","final"]:
    """
    Writer完成后决定是否生成Patch或检查答案。
    """
    if should_propose_patch(state):
        return "patcher"
    if should_review_answer(state):
        return "reviewer"
    return "final"

def route_after_approval(
    state: AgentState
)-> Literal["reviewer","final"]:
    """
    用户接受Patch后进入Reviewer;
    用户拒绝后直接生成最终结果。
    """
    if state["approval_status"] == "approved":
        return "reviewer"
    return "final"
