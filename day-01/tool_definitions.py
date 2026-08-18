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
        "description": (
            "Search the local technical knowledge base, including Unreal Engine "
            "documents and DirectX 12 graphics programming documents. Use this "
            "when the user asks about UE classes, APIs, engine source, rendering, "
            "textures, RHI, GPU resources, or DirectX graphics concepts."
        ),
        "parameters": SearchUEDocsArgs.model_json_schema()
        }
    }
]
