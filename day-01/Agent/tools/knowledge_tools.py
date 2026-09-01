from langchain.tools import tool

from Agent.web_searcher import search_web as project_search_web
from RAG.retriever import search_ue_docs as project_search_ue_docs

@tool("search_ue_docs")
def search_ue_docs_tool(query: str) -> list[dict]:
    """
    搜索本地 Unreal Engine 和 DirectX 技术知识库。

    Args:
        query: UE、DirectX、渲染、RHI、GPU 或纹理相关问题。
    """

    return project_search_ue_docs(query)


@tool("search_web")
def search_web_tool(query: str) -> dict:
    """
    联网搜索实时或公共信息。

    Args:
        query: 需要联网查询的问题，例如新闻、天气、价格或最新版本。
    """

    return project_search_web(query)


KNOWLEDGE_TOOLS = [
    search_ue_docs_tool,
    search_web_tool
]