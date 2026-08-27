from typing import TypedDict
from Agent.schemas import(
    RequestAnalysis,
    CollectedContext,
    DraftAnswer,
    PatchSuggestion,
    ReviewResult
)

class AgentState(TypedDict,total = False):
    """
    LangGraph 所有节点共享的状态.
    total = False 表示这些字段不需要在创建State时一次性全部提供,
    后续节点可以逐步把处理结果写入State.
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
    return{
        "user_request": question,
        "patch_suggestion": None,
        "review": None,
        "timings": {}
    }
    
    
        
