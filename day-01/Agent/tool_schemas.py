from models import (
    ReadFileArgs,
    ListFilesArgs,
    SearchCodeArgs,
    SearchLogsArgs,
    SearchUEDocsArgs,
)


collector_tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a project file. Use this when a specific file path is mentioned or required.",
            "parameters": ReadFileArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files in a project directory.",
            "parameters": ListFilesArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search project source code by keyword.",
            "parameters": SearchCodeArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_logs",
            "description": "Search log files by keyword.",
            "parameters": SearchLogsArgs.model_json_schema()
        }
    }
]


searcher_tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "search_ue_docs",
            "description": "Search local UE / DirectX RAG knowledge base.",
            "parameters": SearchUEDocsArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            # search_ue_error 暂时不注册：当前错误库是早期 mock 数据，先避免 Agent 把它当成可靠证据。
            "name": "search_web",
            "description": "Search the web for real-time or public information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Web search query"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    }
]
