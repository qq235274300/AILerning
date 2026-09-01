import json

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_openai import ChatOpenAI

from Agent.graph.state import AgentState
from Agent.schemas import CollectedContext
from Agent.tools.tool_nodes import ALL_TOOLS
from openai_client import CHAT_MODEL


model = ChatOpenAI(
    model=CHAT_MODEL
)

model_with_tools = model.bind_tools(ALL_TOOLS)

def tool_model_node(state: AgentState) -> AgentState:
    """
    让模型根据 Planner 结果决定具体调用哪个工具。
    """
    analysis = state["analysis"]
    system_prompt = f"""
    你是 Agent 的工具调度节点，只负责收集回答问题所需的上下文。

    Planner 分析：
    {analysis.model_dump_json(indent=2)}

    可用工具：
    - read_file：读取指定文件
    - list_files：列出目录
    - search_code：搜索项目代码
    - search_logs：搜索日志
    - search_ue_docs：搜索 UE / DirectX 本地知识库
    - search_web：搜索实时网络信息

    要求：
    1. 根据 Planner 分析选择必要工具。
    2. 不要调用与问题无关的工具。
    3. 可以一次调用多个互不依赖的工具。
    4. 工具结果不足时，可以继续调用工具。
    5. 上下文足够后，不再调用工具，只回复“上下文收集完成”。
    6. 不要在这个节点生成最终用户答案。
    """
    response = model_with_tools.invoke(
        [
            SystemMessage(content=system_prompt),
            *state["messages"],
        ]
    )
    if response.tool_calls:
        for tool_call in response.tool_calls:
            print(f"Tool call: {tool_call['name']}")
            print(f"Arguments: {tool_call['args']}")
    else:
        print("Tool model: 上下文收集完成")

    return {
        #response 添加到 state["messages"]
        "messages": [response]
    }
    
def parse_tool_content(content):
    """
    ToolNode 通常把 dict/list 工具结果序列化成 JSON 字符串。
    这里将它恢复成 Python 数据。
    """
    if not isinstance(content, str):
        return content

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "content": content
        }

def append_result(target: list, result):
    """
    工具可能返回一个对象，也可能返回对象列表。
    """
    if isinstance(result, list):
        target.extend(result)
    else:
        target.append(result)
        
def build_context_node(state: AgentState) -> AgentState:
    """
    从 ToolMessage 中提取工具执行结果，
    转换成现有 Writer 能使用的 CollectedContext。
    """
    context = CollectedContext()

    for message in state["messages"]:
        if not isinstance(message, ToolMessage):
            continue

        tool_name = message.name
        result = parse_tool_content(message.content)

        if tool_name == "read_file":
            append_result(context.files, result)

        elif tool_name == "list_files":
            context.code_snippets.append({
                "tool": "list_files",
                "result": result,
            })

        elif tool_name == "search_code":
            append_result(context.code_snippets, result)

        elif tool_name == "search_logs":
            append_result(context.logs, result)

        elif tool_name == "search_ue_docs":
            append_result(context.docs, result)

        elif tool_name == "search_web":
            append_result(context.web_results, result)

    print(
        "Context:",
        f"files={len(context.files)},",
        f"code={len(context.code_snippets)},",
        f"logs={len(context.logs)},",
        f"docs={len(context.docs)},",
        f"web={len(context.web_results)}",
    )

    return {
        "context": context
    }