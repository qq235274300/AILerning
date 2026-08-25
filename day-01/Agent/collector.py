import json
from Agent.schemas import RequestAnalysis,CollectedContext
from Agent.tool_runner import run_node_tool_loop
from Agent.tool_schemas import collector_tool_definitions
from tools import read_file,list_files,search_code,search_logs

def extract_keyword(question: str)-> str:
    words = question.replace("，", " ").replace("。", " ").split()
    for word in words:
        if len(word) > 2:
            return word
    return question    

def execute_collector_tool(tool_call):
    args = json.loads(tool_call.function.arguments)
    name = tool_call.function.name
    if name == "read_file":
        return read_file(args["path"])

    if name == "list_files":
        return list_files(args["directory"])

    if name == "search_code":
        return search_code(
            keyword=args["keyword"],
            directory=args.get("directory", "day-01")
        )

    if name == "search_logs":
        return search_logs(
            keyword=args["keyword"],
            directory=args.get("directory", ".")
        )

    return {
        "error": f"Unknown collector tool: {name}"
    }

def collect_context(question: str, analysis: RequestAnalysis) -> CollectedContext:
    context = CollectedContext()
    result = run_node_tool_loop(
        system_prompt=(
            "你是 Collector，只负责收集本地项目上下文，不回答用户问题。"
            "你可以使用 read_file、list_files、search_code、search_logs。"
            "如果用户明确给了文件路径，优先 read_file。"
            "如果用户问某个符号在哪里实现，使用 search_code。"
            "如果用户问日志或 crash，使用 search_logs。"
            "如果不需要本地文件、代码或日志上下文，不要调用工具。"
        ),
        user_prompt=(
            f"用户问题:\n{question}\n\n"
            f"Planner 分析:\n{analysis.model_dump_json(indent=2)}"
        ),
        tools=collector_tool_definitions,
        execute_tool=execute_collector_tool
    )

    for item in result["tool_results"]:
        tool_name = item["tool_name"]
        tool_result = item["result"]

        if tool_name == "read_file":
            context.files.append(tool_result)

        elif tool_name == "search_code":
            context.code_snippets.extend(tool_result)

        elif tool_name == "search_logs":
            context.logs.extend(tool_result)

        elif tool_name == "list_files":
            context.code_snippets.append(tool_result)

    return context