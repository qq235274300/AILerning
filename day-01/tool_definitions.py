# tool_definitions.py
from models import SearchUEErrorArgs

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
    }
]