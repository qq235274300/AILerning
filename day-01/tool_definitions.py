# tool_definitions.py
from models import SearchUEDocsArgs
from models import ReadFileArgs,ListFilesArgs,SearchCodeArgs,SearchLogsArgs

tool_definitions = [
    # search_ue_error 暂时不暴露给模型：当前 ue_error_db 是早期测试数据，信息量太少。
    {
    "type": "function",
    "function": {
        "name": "search_ue_docs",
        "description": (
            "Search the local technical knowledge base, including Unreal Engine "
            "documents and DirectX 12 graphics programming documents. Use this "
            "when the user asks about UE classes, APIs, engine source, rendering, "
            "textures, RHI, GPU resources, or DirectX graphics concepts. "
            "Returned snippets include source, page, distance, and score. "
            "Higher score means more relevant."
        ),
        "parameters": SearchUEDocsArgs.model_json_schema()
        }
    },
    {
    "type": "function",
    "function": {
        "name": "read_file",
        "description": "Read a project file. Use this when analyzing source code or logs.",
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
    },
    {
        "type": "function",
        "function": {
            "name": "read_source_file",
            "description": "Read a source code file for analysis only. This tool never modifies files.",
            "parameters": ReadFileArgs.model_json_schema()
        }
    }

]
