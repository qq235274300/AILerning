from typing import Literal

from langgraph.graph import END, START, StateGraph
from Agent.graph.crash.state import CrashState
from Agent.graph.crash.nodes import (
    read_log_node, extract_error_node, search_docs_node, report_node,
)


def route_after_read(state: CrashState) -> Literal["extract_error", "report"]:
    return "report" if state.get("read_error") else "extract_error"


def build_crash_graph():
    builder = StateGraph(CrashState)
    builder.add_node("read_log", read_log_node)
    builder.add_node("extract_error", extract_error_node)
    builder.add_node("search_docs", search_docs_node)
    builder.add_node("report", report_node)
    builder.add_edge(START, "read_log")
    builder.add_conditional_edges(
        "read_log", route_after_read,
        {"extract_error": "extract_error", "report": "report"},
    )
    builder.add_edge("extract_error", "search_docs")
    builder.add_edge("search_docs", "report")
    builder.add_edge("report", END)
    # 不单独创建 Saver；作为子图调用时使用父图传递的 checkpoint 配置。
    return builder.compile()


crash_graph = build_crash_graph()
