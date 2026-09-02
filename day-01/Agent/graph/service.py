#运行图 并将 LangGraph 内部状态整理成 API 结果。
import json
import time
from pydantic import BaseModel
from Agent.graph.state import create_initial_state
from Agent.graph.workflow import agent_graph

def to_json_value(value):
    """
    递归地把 Pydantic 模型转换成可以被 JSON 序列化的数据。
    """

    if isinstance(value, BaseModel):
        return value.model_dump()

    if isinstance(value, dict):
        return {
            key: to_json_value(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            to_json_value(item)
            for item in value
        ]

    return value


def build_result(
    final_state: dict,
    total_seconds: float
) -> dict:
    """
    把最终 State 整理成同步和流式接口共用的结果。
    """

    return {
        "analysis": to_json_value(
            final_state.get("analysis")
        ),

        "context": to_json_value(
            final_state.get("context")
        ),

        "draft": to_json_value(
            final_state.get("draft")
        ),

        "patch_suggestion": to_json_value(
            final_state.get("patch_suggestion")
        ),

        "review": to_json_value(
            final_state.get("review")
        ),

        "final_answer": final_state.get(
            "final_answer",
            ""
        ),

        "timings": {
            **final_state.get("timings", {}),
            "total": total_seconds
        }
    }


def build_graph_config(thread_id: str):
    """创建 Checkpointer 定位会话所需的运行配置。"""
    return {
        "configurable": {
            "thread_id": thread_id
        },
        "recursion_limit": 10
    }


def run_agent_graph(
    question: str,
    thread_id: str
) -> dict:
    """
    同步执行整张图，完成后一次性返回。
    """
    total_start = time.perf_counter()
    config = build_graph_config(thread_id)

    final_state = agent_graph.invoke(
        create_initial_state(question),
        config=config
    )
    total_seconds = round(
        time.perf_counter() - total_start,
        3
    )
    result = build_result(
        final_state,
        total_seconds
    )
    result["thread_id"] = thread_id
    return result

def stream_event(event: str, data) -> str:
    """
    将一个节点事件转换为一行JSON。
    每条事件末尾添加换行，方便后续使用NDJSON流式输出。
    """
    payload = {
        "event": event,
        "data": to_json_value(data)
    }
    return json.dumps(
        payload,
        ensure_ascii=False
    )+ "\n"

def run_agent_graph_stream(
    question: str,
    thread_id: str
):
    """
    节点流式执行LangGraph。
    每完成一个节点，就产生一条JSON事件。
    """
    total_start = time.perf_counter()

    yield stream_event(
        "graph_start",
        {
            "user_request": question,
            "thread_id": thread_id
        }
    )
    
    config = build_graph_config(thread_id)
    
    for graph_update in agent_graph.stream(
        create_initial_state(question),
        config=config,
        stream_mode="updates"
    ):
        for node_name,node_update in graph_update.items():
            yield stream_event(
                f"{node_name}_done",
                node_update or {}
            )

    snapshot = agent_graph.get_state(config)
    total_seconds = round(
        time.perf_counter() - total_start,
        3
    )

    final_result = build_result(
        snapshot.values,
        total_seconds
    )
    final_result["thread_id"] = thread_id

    yield stream_event(
        "final",
        final_result
    )

if __name__ == "__main__":
    for event_text in run_agent_graph_stream(
        "什么是 Python 列表？",
        "service-demo"
    ):
        print(
            event_text,
            end=""
        )
