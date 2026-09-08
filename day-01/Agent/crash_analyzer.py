from pydantic import BaseModel, Field
from openai_client import client, CHAT_MODEL
from Agent.schemas import CrashReport

# 仅保留子图复用的模型业务函数，流程编排统一放在 graph/crash 中。

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
