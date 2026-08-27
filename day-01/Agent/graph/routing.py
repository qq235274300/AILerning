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

def route_after_planner(state: AgentState) -> Literal["collector", "searcher", "writer"] :
    """
    Planner完成后决定下一个节点。
    """
    if should_collect_context(state):
        return "collector"
    if should_search_knowledge(state):
         return "searcher"
    return "writer"

def route_after_collector(state: AgentState) -> Literal["searcher", "writer"] :
    """
    Collector完成后判断是否还需要搜索知识。
    """
    if should_search_knowledge(state):
         return "searcher"
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