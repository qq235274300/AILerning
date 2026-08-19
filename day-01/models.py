from pydantic import BaseModel,Field
from typing import Literal, List

#用户shuru
class ChatRequest(BaseModel):
    question: str
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
#tool_call
class SearchUEErrorArgs(BaseModel):
    error_message: str = Field(
        ...,description="The Unreal Engine error message"
    )
class SearchUEDocsArgs(BaseModel):
    query: str = Field(
        ...,description="he Unreal Engine topic or API question to search for"
    )
