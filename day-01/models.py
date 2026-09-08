from pydantic import BaseModel,Field
from typing import Literal, List


#用户shuru
class ChatRequest(BaseModel):
    question: str

# Crash 分析接口的请求体，只负责接收 crash log 文件路径。
class CrashRequest(BaseModel):
    path: str

#LLM结构化输出
class UEAnswer(BaseModel):
    type: Literal[
        "compile_error",
        "link_error",
        "runtime_error",
        "reflection_error",
        "concept_explanation",
        "other"
    ]
    reason: str
    solution: List[str]
    code_example: str

#搜索文件模型
class ReadFileArgs(BaseModel):
    path: str = Field(..., description= "File path to read")
class ListFilesArgs(BaseModel):
    directory: str = Field(..., description="Directory path to list")
class SearchCodeArgs(BaseModel):
    keyword: str = Field(..., description="Keyword to search in project code")
    directory: str = Field("day-01",description="Directory to search in")
class SearchLogsArgs(BaseModel):
    keyword: str = Field(...,description="Keyword to search in log files")
    directory: str = Field(".",description="Directory to search logs in")

# Agent 内部状态模型统一使用 Agent.schemas，这里只保留 API/工具请求模型。
class PatchApprovalRequest(BaseModel):
    thread_id: str = Field(
        ...,
        min_length=1,
        max_length=100
    )
    decision: Literal[
        "approve",
        "reject"
    ]
    feedback: str = ""


#tool_call
class SearchUEErrorArgs(BaseModel):
    error_message: str = Field(
        ...,description="The Unreal Engine error message"
    )
class SearchUEDocsArgs(BaseModel):
    query: str = Field(
        ...,description="he Unreal Engine topic or API question to search for"
    )

class AgentRequest(BaseModel):
    question: str
    thread_id: str = Field(
        ...,
        min_length=1,
        max_length=100
    )
