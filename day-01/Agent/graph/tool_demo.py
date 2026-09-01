#python -m Agent.graph.tool_demo
import json

from langchain_core.messages import (
    AIMessage,
    ToolMessage,
)
from langgraph.graph import (
    END,
    START,
    MessagesState,
    StateGraph,
)

from Agent.tools.tool_nodes import local_tools_node



def build_local_tools_demo_graph():
    """
    创建只有本地只读 ToolNode 的测试图。
    """
    builder = StateGraph(MessagesState)
    builder.add_node(
        "local_tools",
        local_tools_node
    )
    builder.add_edge(
        START,
        "local_tools"
    )
    builder.add_edge(
        "local_tools",
        END
    )
    return builder.compile()

local_tools_demo_graph  = build_local_tools_demo_graph()

def print_tool_message(message: ToolMessage):
    """
    将 ToolMessage 中的 JSON 字符串格式化输出。
    """

    print(f"\n工具：{message.name}")
    print(f"调用 ID：{message.tool_call_id}")

    try:
        content = json.loads(
            message.content
        )

        print(
            json.dumps(
                content,
                ensure_ascii=False,
                indent=2
            )
        )
    except json.JSONDecodeError:
        print(message.content)
    
def run_demo():
    tool_calls = [
        {
            "name": "read_file",
            "args": {
                "path": "day-01/Agent/graph/state.py"
            },
            "id": "day72_read_file",
            "type": "tool_call"
        },
        {
            "name": "list_files",
            "args": {
                "directory": "day-01/Agent/graph"
            },
            "id": "day72_list_files",
            "type": "tool_call"
        },
        {
            "name": "search_code",
            "args": {
                "keyword": "StateGraph",
                "directory": "day-01/Agent/graph"
            },
            "id": "day72_search_code",
            "type": "tool_call"
        },
        {
            "name": "search_logs",
            "args": {
                "keyword": "Fatal error",
                "directory": "day-01/TestLogs"
            },
            "id": "day72_search_logs",
            "type": "tool_call"
        }
    ]

    ai_message = AIMessage(
        content="",
        tool_calls=tool_calls
    )

    result = local_tools_demo_graph.invoke(
        {
            "messages": [
                ai_message
            ]
        }
    )

    for message in result["messages"]:
        if isinstance(message, ToolMessage):
            print_tool_message(message)


if __name__ == "__main__":
    run_demo()
