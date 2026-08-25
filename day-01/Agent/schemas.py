from pydantic import BaseModel, Field
from typing import List,Literal,Optional


class CrashReport(BaseModel):
    crash_type: str = Field(..., description="Crash 类型，例如 runtime_error / access_violation / assert / ensure / unknown")
    summary: str = Field(..., description="Crash 的一句话总结")
    error_message: str = Field(..., description="从日志中提取出的核心错误信息")
    possible_causes: List[str] = Field(default_factory=list, description="可能原因")
    evidence: List[str] = Field(default_factory=list, description="日志或文档中的证据")
    recommended_fixes: List[str] = Field(default_factory=list, description="建议修复方向")
    references: List[str] = Field(default_factory=list, description="引用来源，例如日志行号、UE 文档 source/page")

class ToolNodeResult(BaseModel):
    messages: List[dict] = Field(default_factory=list)
    tool_results: List[dict] = Field(default_factory=list)

class RequestAnalysis(BaseModel):
    task_type: Literal[
        "code_analysis",
        "crash_analysis",
        "log_analysis",
        "ue_api_question",
        "general"
    ] = Field(..., description="用户问题类型")
    
    needs_file_context: bool = Field(...,description="是否需要读取或搜索项目文件")
    needs_logs_context: bool = Field(...,description="是否需要搜索日志")
    needs_rag_context: bool = Field(...,description="是否需要搜索UE / DX 知识库")
    needs_web_search: bool = Field(False,description="是否需要联网搜索实时或公共信息")
    needs_review: bool = Field(False,description="是否需要 Reviewer 检查答案，代码分析、Crash 分析等高风险任务应为 True")
    file_paths: List[str] = Field(
        default_factory=list, #会默认创建
        description="用户明确提到的文件路径"
    )
    search_keywords: List[str] = Field(
        default_factory=list,
        description="用于搜索代码、日志、知识库的关键词"
    )
    
class CollectedContext(BaseModel):
    files: List[dict] = Field(default_factory=list) #字典
    code_snippets: List[dict] = Field(default_factory=list)
    logs: List[dict]= Field(default_factory=list)
    docs: List[dict] = Field(default_factory=list)
    ue_errors: List[dict] = Field(default_factory=list)
    web_results: List[dict] = Field(default_factory=list)

class DraftAnswer(BaseModel): #草稿答案(初步)
    answer: str
    references: List[str] = Field(default_factory=list)
    
class ReviewResult(BaseModel): 
    passed: bool
    issues: List[str] = Field(default_factory=list)
    final_answer: str
