from langgraph.prebuilt import ToolNode
from Agent.tools.local_tools import LOCAL_TOOLS
from Agent.tools.knowledge_tools import KNOWLEDGE_TOOLS


local_tools_node = ToolNode(
    LOCAL_TOOLS,
    handle_tool_errors=True
)

knowledge_tools_node = ToolNode(
    KNOWLEDGE_TOOLS,
    handle_tool_errors=True
)

ALL_TOOLS = [
    *LOCAL_TOOLS,
    *KNOWLEDGE_TOOLS
]

all_tools_node = ToolNode(
    ALL_TOOLS,
    handle_tool_errors=True
)