from langchain_core.messages import (
    AIMessage,
    HumanMessage,
)


def find_current_turn_start(messages) -> int:
    """找到最后一条 HumanMessage，也就是本轮起点。"""
    for index in range(len(messages) - 1, -1, -1):
        if isinstance(messages[index], HumanMessage):
            return index

    return 0


def get_current_turn_messages(messages):
    """只返回本轮 Human、AI 和 Tool 消息。"""
    start = find_current_turn_start(messages)
    return messages[start:]


def format_conversation_history(
    messages,
    max_messages: int = 6,
) -> str:
    """保留用户消息和最终答案，跳过旧 ToolMessage。"""
    current_start = find_current_turn_start(messages)
    history = []

    for message in messages[:current_start]:
        if isinstance(message, HumanMessage):
            history.append(f"用户：{message.content}")

        elif (
            isinstance(message, AIMessage)
            and not message.tool_calls
            and message.content
            and message.content != "上下文收集完成"
        ):
            history.append(f"助手：{message.content}")

    return "\n".join(history[-max_messages:])
