from pydantic import BaseModel, Field
from openai_client import client, CHAT_MODEL
from RAG.retriever import search_ue_docs
from Agent.schemas import CrashReport
from tools import read_log

#检查UE Crash专用流程

class ErrorSummary(BaseModel):
    crash_type: str = Field(..., description="Crash 类型")
    error_message: str = Field(..., description="核心错误信息")
    callstack: list[str] = Field(default_factory=list, description="关键调用栈")
    keywords: list[str] = Field(default_factory=list, description="用于搜索 UE 文档的关键词")
    
    
def extract_error_summary(log_text: str) -> ErrorSummary:
    response = client.chat.completions.parse(
        model= CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 UE Crash 日志分析器。"
                    "只提取日志中的关键信息，不要生成修复建议。"
                    "重点关注 Fatal error、Assertion failed、ensure、Access violation、callstack、模块名、类名、函数名。"
                )
            },
            {
                "role": "user",
                "content": log_text
            }
        ],
        response_format= ErrorSummary   
    )
    return response.choices[0].message.parsed

def collect_crash_knowledge(error_summary: ErrorSummary):
    # 暂时不使用 search_ue_error：当前错误库只是早期 mock 数据，内容太少，容易误导 Crash 分析。
    docs_result = search_ue_docs(
        "".join(error_summary.keywords)
    )
    return {
        "docs_result": docs_result
    }

def generate_crash_report(
    log_path: str,
    error_summary: ErrorSummary,
    knowledge: dict
)-> CrashReport:
    response = client.chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 UE Crash 分析 Agent。"
                    "根据 crash 日志摘要和 UE 文档搜索结果，生成结构化 Crash 报告。"
                    "不要生成 patch，不要假装已经修改代码。"
                    "如果证据不足，要明确说明不确定。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"日志路径:\n{log_path}\n\n"
                    f"错误摘要:\n{error_summary.model_dump_json(indent=2)}\n\n"
                    f"知识库搜索结果:\n{knowledge}"
                )
            }
        ],
        response_format=CrashReport
    )
    return response.choices[0].message.parsed

def run_crash_agent(log_path: str) -> CrashReport:
    log_result = read_log(log_path)

    if "error" in log_result:
        return CrashReport(
            crash_type="unknown",
            summary=log_result["error"],
            error_message="",
            possible_causes=[],
            evidence=[],
            recommended_fixes=[],
            references=[]
        )

    error_summary = extract_error_summary(log_result["content"])

    knowledge = collect_crash_knowledge(error_summary)

    report = generate_crash_report(
        log_path=log_path,
        error_summary=error_summary,
        knowledge=knowledge
    )

    return report
