"""Graph 的同步、暂停和恢复接口。"""
import json
import time
from pydantic import BaseModel
from langgraph.types import Command, Interrupt
from Agent.graph.state import create_initial_state
from Agent.graph.workflow import agent_graph


def to_json_value(value):
    if isinstance(value, Interrupt):
        return {"id": value.id, "value": to_json_value(value.value)}
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {key: to_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_json_value(item) for item in value]
    return value


def build_result(final_state: dict, total_seconds: float) -> dict:
    result = {
        key: to_json_value(final_state.get(key))
        for key in (
            "analysis", "context", "draft", "patch_suggestion", "review",
            "approval_status", "approval_feedback",
        )
    }
    result["final_answer"] = final_state.get("final_answer", "")
    result["timings"] = {**final_state.get("timings", {}), "total": total_seconds}
    return result


def build_graph_config(thread_id: str):
    # 这是整张图的步数预算，包含工具循环和审查节点。
    return {"configurable": {"thread_id": thread_id}, "recursion_limit": 25}


def pending_interrupts(snapshot):
    return [item for task in snapshot.tasks for item in task.interrupts]


def approval_payload(thread_id, interrupts):
    return {"thread_id": thread_id, "interrupts": to_json_value(interrupts)}


def run_agent_graph(question: str, thread_id: str) -> dict:
    start = time.perf_counter()
    config = build_graph_config(thread_id)
    # 审批期间不允许新问题覆盖原来的暂停任务。
    if not pending_interrupts(agent_graph.get_state(config)):
        agent_graph.invoke(create_initial_state(question), config=config)
    snapshot = agent_graph.get_state(config)
    pending = pending_interrupts(snapshot)
    result = build_result(snapshot.values, round(time.perf_counter() - start, 3))
    result.update(approval_payload(thread_id, pending))
    result["status"] = "approval_required" if pending else "completed"
    return result


def stream_event(event: str, data) -> str:
    return json.dumps(
        {"event": event, "data": to_json_value(data)}, ensure_ascii=False
    ) + "\n"


def stream_graph(input_value, thread_id):
    """新请求和恢复请求共用流处理，暂停时不发送 final。"""
    start = time.perf_counter()
    config = build_graph_config(thread_id)
    try:
        for update in agent_graph.stream(input_value, config=config, stream_mode="updates"):
            for name, value in update.items():
                if name != "__interrupt__":
                    yield stream_event(f"{name}_done", value or {})
        # 完整消费 stream 后读取真实快照，避免手动合并 messages。
        snapshot = agent_graph.get_state(config)
        pending = pending_interrupts(snapshot)
        if pending:
            yield stream_event("approval_required", approval_payload(thread_id, pending))
            return
        result = build_result(snapshot.values, round(time.perf_counter() - start, 3))
        result.update({"thread_id": thread_id, "status": "completed"})
        yield stream_event("final", result)
    except Exception:
        import logging
        logging.getLogger(__name__).exception("Graph execution failed")
        yield stream_event("graph_error", {"message": "运行失败，请检查服务端日志。"})


def run_agent_graph_stream(question: str, thread_id: str):
    pending = pending_interrupts(agent_graph.get_state(build_graph_config(thread_id)))
    if pending:
        yield stream_event("approval_required", approval_payload(thread_id, pending))
        return
    yield stream_event("graph_start", {"user_request": question, "thread_id": thread_id})
    yield from stream_graph(create_initial_state(question), thread_id)


def resume_agent_graph_stream(thread_id: str, decision: str, feedback: str = ""):
    snapshot = agent_graph.get_state(build_graph_config(thread_id))
    pending = pending_interrupts(snapshot)
    if decision not in {"approve", "reject"} or not pending or "approval" not in snapshot.next:
        yield stream_event("resume_error", {"message": "当前会话没有待确认的 Patch，或决定无效。"})
        return
    yield stream_event("graph_resumed", {"thread_id": thread_id})
    # 使用中断 ID 恢复原节点，不创建新一轮 State。
    command = Command(resume={pending[0].id: {"decision": decision, "feedback": feedback}})
    yield from stream_graph(command, thread_id)


if __name__ == "__main__":
    for event in run_agent_graph_stream("什么是 Python 列表？", "service-demo"):
        print(event, end="")
