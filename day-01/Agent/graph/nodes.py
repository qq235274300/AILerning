from Agent.graph.state import AgentState
from Agent.schemas import CollectedContext

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
   
