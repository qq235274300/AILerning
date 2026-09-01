from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import tools_condition

from Agent.tools.tool_nodes import ALL_TOOLS, all_tools_node
from openai_client import CHAT_MODEL

SYSTEM_PROMPT = """
你是一个能够分析本地代码、查询技术知识库和搜索网络的 Agent。

请根据用户问题自行判断是否需要调用工具：

1. 需要读取项目文件时，调用 read_file。
2. 需要列出目录时，调用 list_files。
3. 需要搜索项目代码时，调用 search_code。
4. 需要搜索日志时，调用 search_logs。
5. Unreal Engine 或 DirectX 技术问题需要文档依据时，调用 search_ue_docs。
6. 需要实时信息或互联网资料时，调用 search_web。
7. 普通知识问题不需要工具，可以直接回答。

工具执行结束后，需要根据工具返回的信息继续回答用户。
不要编造没有从工具结果中获得的文件内容、日志内容或引用来源。
"""

#bind tools
model = ChatOpenAI(
    model=CHAT_MODEL
)
# bind_tools 会把工具名称、说明和参数结构提交给模型。
model_with_tools = model.bind_tools(ALL_TOOLS)

def model_node(state: MessagesState):
    """
    调用模型，让模型决定：
    1. 直接回答；
    2. 或者生成 tool_calls。
    """
    
    response = model_with_tools.invoke(
        [
            SystemMessage(content=SYSTEM_PROMPT),
            *state["messages"],
        ]
    )
    if response.tool_calls:
        print("模型决定调用工具：")

        for tool_call in response.tool_calls:
            print(f"工具名称：{tool_call['name']}")
            print(f"工具参数：{tool_call['args']}")
    else:
        print("模型没有调用工具，准备直接回答。")

    return {
        "messages": [response]
    }
    
def build_tool_calling_graph():
    builder = StateGraph(MessagesState)
    
    builder.add_node("model",model_node)
    builder.add_node("tools",all_tools_node)
    builder.add_edge(
        START,
        "model"
    )
    #检查模型返回的AI Message中是否存在tool_calls
    builder.add_conditional_edges(
        "model",
        tools_condition,
        {
            "tools": "tools",
            "__end__": END,
        }
    )
    builder.add_edge("tools","model")
    
    return builder.compile()

tool_calling_graph = build_tool_calling_graph()

def run_demo(question: str):
    result = tool_calling_graph.invoke(
        {
            "messages": [
                HumanMessage(content=question)
            ]
        },
        config={
            "recursion_limit": 8
        },
    )
    print("\n完整消息流程：")

    for message in result["messages"]:
        message.pretty_print()

    print("\n最终回答：")
    print(result["messages"][-1].content)

    return result

if __name__ == "__main__":
    run_demo(
        "读取 day-01/Agent/graph/state.py，并解释 AgentState 保存了哪些数据"
    )