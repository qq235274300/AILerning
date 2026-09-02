from Agent.graph.state import AgentState
from Agent.schemas import CollectedContext
from Agent.planner import analyze_request
from Agent.collector import collect_context
from Agent.searcher import search_knowledge
from Agent.patcher import propose_patch
from Agent.reviewer import review_answer
from Agent.writer import generate_suggestion
from langchain_core.messages import AIMessage
from Agent.graph.message_utils import (
    format_conversation_history,
)
"""
Node = 一个普通的python函数
输入： 当前State
输出:  需要更新的部分State
"""

def build_question_with_history(state: AgentState) -> str:
    history = format_conversation_history(state["messages"])
    if not history:
        return state["user_request"]

    return (
        f"历史对话：\n{history}\n\n"
        f"当前问题：\n{state['user_request']}"
    )
    
def planner_node(state: AgentState)-> AgentState:
    print("LangGraph node: planner")
    """
    Planner节点。
    读取用户问题，调用现有analyze_request(),
    将结构化分析结果写入analysis.
    """
    analysis = analyze_request(build_question_with_history(state))
    return{
        "analysis": analysis
    }
    
def writer_node(state: AgentState) -> AgentState:
    print("LangGraph node: writer")
    """
    Write节点。
    读取用户问题，Planner分析和已收集上下文，
    调用现有 generate_suggestion()生成草稿.
    """
    analysis = state["analysis"]
    context = state["context"]
    
    draft = generate_suggestion(
        question=build_question_with_history(state),
        analysis=analysis,
        context=context
    )
    return{
        "draft": draft
    }
    
def collector_node(state: AgentState) -> AgentState:
    """
    收集项目文件、代码和日志上下文。
    """
    print("LangGraph node: collector")
    context = collect_context(
        question=state["user_request"],
        analysis=state["analysis"]
    )
    return {
        "context": context
    }

def searcher_node(state: AgentState) -> AgentState:
    """
    根据Planner判断搜索RAG 或 Web.
    """
    print("LangGraph node: searcher")
    context = search_knowledge(
        question=state["user_request"],
        analysis=state["analysis"],
        context=state["context"]
    )
    return {
        "context": context
    }
    
def patcher_node(state: AgentState) -> AgentState:
    """
    根据代码分析结果生成Patch建议。
    只生成建议，不真实修改文件。
    """
    print("LangGraph node: patcher")
    patch_suggestion = propose_patch(
        question=state["user_request"],
        analysis=state["analysis"],
        context=state["context"],
        draft=state["draft"]
    )
    return {
        "patch_suggestion": patch_suggestion
    }
    
def reviewer_node(state: AgentState) -> AgentState:
    """
    检查Writer答案和可选的Patch建议。
    """
    print("LangGraph node: reviewer")
    review = review_answer(
        question=state["user_request"],
        analysis=state["analysis"],
        context=state["context"],
        draft=state["draft"],
        patch_suggestion=state.get("patch_suggestion")
    )
    return {
        "review": review
    }
    
def final_node(state: AgentState) -> AgentState:
    """
    选择最终返回给用户的答案。
    该节点不调用OpenAI。
    """
    print("LangGraph node: final")
    review = state.get("review")
    if review is not None:
        final_answer = review.final_answer
    else:
        final_answer = state["draft"].answer
    
    return {
        "final_answer": final_answer,
        "messages": [
            AIMessage(content=final_answer)
        ]
    }
        
