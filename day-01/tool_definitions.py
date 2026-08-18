# tool_definitions.py
from models import SearchUEErrorArgs,SearchUEDocsArgs

tool_definitions = [

    {
        "type": "function",
        "function": {

            "name": "search_ue_error",

            "description":
            "Search Unreal Engine error database. "
            "Use this tool when user asks about UE errors.",
            "parameters": SearchUEErrorArgs.model_json_schema()           
        }
    },
    {
    "type": "function",
    "function": {
        "name": "search_ue_docs",
        "description": "Search Unreal Engine documentation knowledge base. Use this when the user asks about UE classes, APIs, engine source, or usage details.",
        "parameters": SearchUEDocsArgs.model_json_schema()
        }
    }
]