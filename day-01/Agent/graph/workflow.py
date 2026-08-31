#定义图
from langgraph.graph import END,START,StateGraph    
from Agent.graph.state import AgentState
from Agent.graph.nodes import (
    planner_node,
    collector_node,
    searcher_node,
    writer_node,
    patcher_node,
    reviewer_node,
    final_node,
)
from Agent.graph.routing import (
    route_after_planner,
    route_after_collector,
    route_after_writer,
)

def build_agent_graph():
    """
    创建包含动态路由的 Agent 图。
    """

    builder = StateGraph(AgentState)

    builder.add_node(
        "planner",
        planner_node
    )
    
    builder.add_node(
        "collector",
        collector_node
    )

    builder.add_node(
        "searcher",
        searcher_node
    )

    builder.add_node(
        "writer",
        writer_node
    )
    builder.add_node(
        "patcher",
        patcher_node
    )

    builder.add_node(
        "reviewer",
        reviewer_node
    )

    builder.add_node(
        "final",
        final_node
    )

    builder.add_edge(
        START,
        "planner"
    )

    builder.add_conditional_edges(
        "planner",
        route_after_planner,
        {
           "collector": "collector",
           "searcher": "searcher",
           "writer": "writer"
        }
    )
    
    builder.add_conditional_edges(
        "collector",
        route_after_collector,
        {
            "searcher": "searcher",
            "writer": "writer"
        }
    )
    
    builder.add_edge(
        "searcher",
        "writer",
    )

    builder.add_conditional_edges(
        "writer",
        route_after_writer,
        {
            "patcher": "patcher",
            "reviewer": "reviewer",
            "final": "final"
        }
    )
    
    builder.add_edge(
        "patcher",
        "reviewer"
    )

    builder.add_edge(
        "reviewer",
        "final"
    )

    builder.add_edge(
        "final",
        END
    )

    return builder.compile()    

agent_graph = build_agent_graph()
