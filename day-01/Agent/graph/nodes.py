from Agent.graph.state import AgentState
from Agent.schemas import CollectedContext
from Agent.planner import analyze_request
from Agent.writer import generate_suggestion

"""
Node = 一个普通的python函数
输入： 当前State
输出:  需要更新的部分State
"""

def normalize_question_node(state: AgentState)-> AgentState:
    """
    清理用户问题前后的空格。
    节点读取user_request,然后只返回需要更新的 user_request
    """
    question = state["user_request"].strip()
    return{
        "user_request": question
    }
    
def initialize_context_node(state: AgentState) -> AgentState:
    """
    为后续Collector 和 Searcher创建空的上下文
    目前不读取文件 不搜索向量库，
    只演示节点如何向State添加新字段。
    """
    return{
        "context": CollectedContext()
    }
    
def planner_node(state: AgentState)-> AgentState:
    """
    Planner节点。
    读取用户问题，调用现有analyze_request(),
    将结构化分析结果写入analysis.
    """
    question = state["user_request"]
    analysis = analyze_request(question)
    return{
        "analysis": analysis
    }
    
def writer_node(state: AgentState) -> AgentState:
    """
    Write节点。
    读取用户问题，Planner分析和已收集上下文，
    调用现有 generate_suggestion()生成草稿.
    """
    question = state["user_request"]
    analysis = state["analysis"]
    context = state["context"]
    
    draft = generate_suggestion(
        question=question,
        analysis=analysis,
        context=context
    )
    return{
        "draft": draft
    }
    
