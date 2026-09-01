from typing import TypedDict
from langgraph.graph import MessagesState
from langchain_core.messages import HumanMessage
from Agent.schemas import(
    RequestAnalysis,
    CollectedContext,
    DraftAnswer,
    PatchSuggestion,
    ReviewResult
)

class AgentState(MessagesState,total = False):
    """
    LangGraph 所有节点共享的状态.
    MessagesState 提供：
        messages: list[AnyMessage]
    其他字段保存项目自己的业务状态。
    """
    #本次用户提交的问题
    user_request : str
    #Planner对问题类型及上下文需求的判断
    analysis : RequestAnalysis
    #Collector 和 Searcher收集到的文件，日志，RAG，Web等上下文
    context: CollectedContext
    #Writer生成的初步答案
    draft : DraftAnswer
    #Patcher 生成的修改建议，普通问题可能没有Patch
    patch_suggestion: PatchSuggestion | None
    #Reviewer的检查结果 普通问题会跳过Reviewer
    review: ReviewResult | None
    #最终返回用户的答案
    final_answer: str
    #记录每个节点运行时间
    timings: dict[str,float]

#? Graph有什么办法约定回复格式
def create_initial_state(question: str)-> AgentState:
    """
    根据用户提问创建一次新的Agent初始状态
    """
    question = question.strip()
    return{
        "user_request": question,
        #tool Calling使用的消息历史
        "messages": [
            HumanMessage(content= question)
        ],
        "context": CollectedContext(),
        "patch_suggestion": None,
        "review": None,
        "timings": {}
    }
    
    
        
