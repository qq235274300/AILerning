from langgraph.graph import END,START,StateGraph    
from Agent.graph.nodes import normalize_question_node,initialize_context_node
from Agent.graph.state import create_initial_state,AgentState
from pathlib import Path

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
    
demo_graph = build_demo_graph()

if __name__ == "__main__":
    initial_state = create_initial_state(
        "UE 中什么时候应该让一个类继承自 UObject？UObject 和普通 C++ 类有什么区别"
    )
    result = demo_graph.invoke(initial_state)
    
    print(result)
    
    image_path = (
        Path(__file__).parent
        / "workflow_graph.png"
    )
    demo_graph.get_graph().draw_mermaid_png(
        output_file_path=str(image_path)
    )

    print(f"图已生成: {image_path}")