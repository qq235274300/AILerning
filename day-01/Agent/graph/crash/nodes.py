from Agent.crash_analyzer import extract_error_summary, generate_crash_report
from Agent.graph.crash.state import CrashState
from Agent.schemas import CrashReport
from RAG.retriever import search_ue_docs
from tools import read_log


def read_log_node(state: CrashState) -> dict:
    print("Crash node: read_log")
    # 复用只读工具：当前工具返回日志末尾 20000 个字符，不是完整日志。
    try:
        result = read_log(state["log_path"])
    except (OSError, ValueError) as error:
        return {"log_text": "", "read_error": str(error)}
    if "error" in result:
        return {"log_text": "", "read_error": result["error"]}
    text = result["content"]
    return {
        "log_text": text,
        "read_error": "" if text.strip() else "日志为空，无法分析。",
    }


def extract_error_node(state: CrashState) -> dict:
    print("Crash node: extract_error")
    summary = extract_error_summary(state["log_text"])
    if summary is None:
        raise ValueError("模型没有返回有效的 Crash 摘要。")
    return {"error_summary": summary}


def search_docs_node(state: CrashState) -> dict:
    print("Crash node: search_docs")
    summary = state["error_summary"]
    # 关键词之间保留空格；没有关键词时使用核心错误作为检索词。
    query = " ".join(summary.keywords).strip() or summary.error_message.strip()
    docs = search_ue_docs(query) if query else []
    return {"knowledge": {"docs_result": docs}}


def report_node(state: CrashState) -> dict:
    print("Crash node: report")
    # 读取失败时直接返回明确的错误，不调用模型或消耗检索费用。
    if state.get("read_error"):
        report = CrashReport(
            crash_type="unknown", summary=state["read_error"], error_message=""
        )
    else:
        report = generate_crash_report(
            log_path=state["log_path"],
            error_summary=state["error_summary"],
            knowledge=state["knowledge"],
        )
        if report is None:
            raise ValueError("模型没有返回有效的 Crash 报告。")
    return {"report": report}
