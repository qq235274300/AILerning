from pydantic import BaseModel, Field
from typing import List,Literal,Optional

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

class DraftAnswer(BaseModel): #草稿答案(初步)
    answer: str
    references: List[str] = Field(default_factory=list)
    
class ReviewResult(BaseModel): 
    passed: bool
    issues: List[str] = Field(default_factory=list)
    final_answer: str