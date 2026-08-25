import json

from Agent.schemas import RequestAnalysis, CollectedContext
from Agent.tool_runner import run_node_tool_loop
from Agent.tool_schemas import searcher_tool_definitions
from Agent.web_searcher import search_web
from RAG.retriever import search_ue_docs

def execute_searcher_tool(tool_call):
    args = json.loads(tool_call.function.arguments)
    name = tool_call.function.name

    if name == "search_ue_docs":
        return search_ue_docs(args["query"])

    if name == "search_web":
        return search_web(args["query"])

    return {
        "error": f"Unknown searcher tool: {name}"
    }

def search_knowledge(question: str, analysis: RequestAnalysis, context: CollectedContext) -> CollectedContext:
    result = run_node_tool_loop(
        system_prompt=(
            "你是 Searcher，只负责搜索知识，不直接回答用户问题。"
            "你可以使用 search_ue_docs、search_web。"
            "UE、DirectX、渲染、RHI、GPU、纹理相关问题优先使用 search_ue_docs。"
            "UE 报错或 crash 相关问题也优先使用 search_ue_docs 查询本地技术文档。"
            "实时信息、新闻、天气、选举、最新版本、价格、政策变化等问题使用 search_web。"
            "如果不需要知识库或联网搜索，不要调用工具。"
        ),
        user_prompt=(
            f"用户问题:\n{question}\n\n"
            f"Planner 分析:\n{analysis.model_dump_json(indent=2)}\n\n"
            f"已收集的本地上下文:\n{context.model_dump_json(indent=2)}"
        ),
        tools=searcher_tool_definitions,
        execute_tool=execute_searcher_tool,
        # Searcher 调用 RAG / Web 工具拿到知识后即可结束，避免再调用一次模型确认。
        stop_after_tool_calls=True
    )

    for item in result["tool_results"]:
        tool_name = item["tool_name"]
        tool_result = item["result"]

        if tool_name == "search_ue_docs":
            context.docs.extend(tool_result)

        elif tool_name == "search_web":
            context.web_results.append(tool_result)

    return context
