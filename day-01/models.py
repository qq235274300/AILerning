from pydantic import BaseModel,Field

#用户shuru
class ChatRequest(BaseModel):
    question: str
#LLM结构化输出
class UEAnswer(BaseModel):
    reason: str
    solution: str
    code_example: str
#tool_call
class SearchUEErrorArgs(BaseModel):
    error_message: str = Field(
        ...,description="The Unreal Engine error message"
    )
