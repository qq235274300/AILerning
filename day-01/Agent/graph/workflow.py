from pathlib import Path
from langgraph.graph import END,START,StateGraph    
from Agent.graph.nodes import normalize_question_node,initialize_context_node
from Agent.graph.state import create_initial_state,AgentState
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

def  build_demo_graph():
    #创建图的构建器 并规定所有节点共享AgentState
    builder = StateGraph(AgentState)
    #注册节点: 第一个参数是节点名称 第二个参数是节点函数
    builder.add_node(
        "normalize_question",
        normalize_question_node
    )
    builder.add_node(
        "initialize_context",
        initialize_context_node
    )
    #定义固定执行顺序
    builder.add_edge(
        START,
        "normalize_question"
    )
    builder.add_edge(
         "normalize_question",
         "initialize_context"
    )
    builder.add_edge(
        "initialize_context",
        END
    )
    #compile 会检查图结构 并生成真正可运行的图
    return builder.compile()

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

if __name__ == "__main__":
    initial_state = create_initial_state(
        "UE 中什么时候应该让一个类继承自 UObject？UObject 和普通 C++ 类有什么区别"
    )
    result = agent_graph.invoke(initial_state)
    
    print("\nPlanner 分析：")
    print(
        result["analysis"].model_dump_json(indent=2)
    )

    print("\nWriter 草稿：")
    print(result["draft"].answer)

    print("\n引用来源：")
    print(result["draft"].references)
    
    print("\n最终答案：")
    print(result["final_answer"])

    print("\nPatch 建议：")
    print(result.get("patch_suggestion"))

    print("\nReviewer 结果：")
    print(result.get("review"))
    
    image_path = (
        Path(__file__).parent
        / "workflow_graph.png"
    )
    agent_graph.get_graph().draw_mermaid_png(
        output_file_path=str(image_path)
    )

    print(f"图已生成: {image_path}")