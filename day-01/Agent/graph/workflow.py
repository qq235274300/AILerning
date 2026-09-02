#定义图
from langgraph.graph import END,START,StateGraph    
from langgraph.prebuilt import tools_condition
from Agent.graph.tool_agent import (
    tool_model_node,
    build_context_node,
)
from Agent.tools.tool_nodes import all_tools_node
from Agent.graph.state import AgentState
from Agent.graph.nodes import (
    planner_node,
    writer_node,
    patcher_node,
    reviewer_node,
    final_node,
)
from Agent.graph.routing import (
    route_after_planner,
    route_after_writer,
)
from langgraph.checkpoint.memory import InMemorySaver


checkpointer = InMemorySaver()

def build_agent_graph():
    builder = StateGraph(AgentState)

    builder.add_node("planner", planner_node)
    builder.add_node("tool_model", tool_model_node)
    builder.add_node("tools", all_tools_node)
    builder.add_node("build_context", build_context_node)
    builder.add_node("writer", writer_node)
    builder.add_node("patcher", patcher_node)
    builder.add_node("reviewer", reviewer_node)
    builder.add_node("final", final_node)

    builder.add_edge(START, "planner")

    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
            "tool_model": "tool_model",
            "writer": "writer",
        },
    )

    # 有 tool_calls 就执行工具。
    # 没有 tool_calls 时，不直接 END，而是整理上下文。
    builder.add_conditional_edges(
        "tool_model",
        tools_condition,
        {
            "tools": "tools",
            "__end__": "build_context",
        },
    )

    # 工具执行结果重新交给模型，
    # 模型可以继续调用工具或宣布收集完成。
    builder.add_edge("tools", "tool_model")

    builder.add_edge("build_context", "writer")

    builder.add_conditional_edges(
        "writer",
        route_after_writer,
        {
            "patcher": "patcher",
            "reviewer": "reviewer",
            "final": "final",
        },
    )

    builder.add_edge("patcher", "reviewer")
    builder.add_edge("reviewer", "final")
    builder.add_edge("final", END)

    return builder.compile(
        checkpointer=checkpointer
    )

agent_graph = build_agent_graph()
