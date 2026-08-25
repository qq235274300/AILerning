import json
from typing import Callable, List

from openai_client import CHAT_MODEL, TOOL_LOOP_MAX_COMPLETION_TOKENS, client

def run_node_tool_loop(
    system_prompt: str,
    user_prompt: str,
    tools: List[dict],
    execute_tool: Callable,
    max_steps: int = 5 
):
    messages = [
        {
            "role" : "system",
            "content": system_prompt
        },
         {
            "role" : "user",
            "content": user_prompt
        }
    ]
    tool_results = []
    
    for _ in range(max_steps):
        response = client.chat.completions.create(
            model= CHAT_MODEL,
            messages= messages,
            max_completion_tokens= TOOL_LOOP_MAX_COMPLETION_TOKENS,
            tools= tools,
            tool_choice="auto"
        )
        
        message = response.choices[0].message
        
        if not message.tool_calls:
            messages.append(message)
            return {
                "messages":[
                    message.model_dump()
                    if hasattr(message,"model_dump")
                    else message
                    for message in messages
                ],
                "tool_results":tool_results
            }
        messages.append(message)
        
        for tool_call in message.tool_calls:
            print(f"Tool call: {tool_call.function.name}")
            print(f"Arguments: {tool_call.function.arguments}")
            result = execute_tool(tool_call)
            tool_results.append(
                {
                    "tool_name": tool_call.function.name,
                    "arguments": tool_call.function.arguments,
                    "result": result                   
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                }
            )
    
    return {
        "messages":[
            message.model_dump()
            if hasattr(message, "model_dump")
            else message
            for message in messages
        ],
        "tool_results": tool_results
    }
