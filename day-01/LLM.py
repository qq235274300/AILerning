from models import UEAnswer
from openai_client import (
    CHAT_MODEL,
    FINAL_MAX_COMPLETION_TOKENS,
    TOOL_LOOP_MAX_COMPLETION_TOKENS,
    client,
)
from prompt import SYSTEM_PROMPT
from tools import search_ue_error,read_file,list_files,search_code,search_logs
from RAG.retriever import search_ue_docs
from tool_definitions import tool_definitions
import json

def execute_tool(tool_call):
    args = json.loads(tool_call.function.arguments)
    name = tool_call.function.name
    if name == "search_ue_error":       
        return search_ue_error(args["error_message"] ) 
    if name == "search_ue_docs":       
            return search_ue_docs(args["query"] )
    if name == "read_file":
        return read_file(args["path"])
    if name == "list_files":
        return list_files(args["directory"])
    if name == "search_code":
        return search_code(
            args["keyword"],
            args.get("directory", "day-01")
        )
    if name == "search_logs":
        return search_logs(
            args["keyword"],
            args.get("directory", ".")
        )
    return {"error": f"Unknown tool: {name}"}

chat_history = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

def run_tool_loop(chat_history, max_steps = 5):
    for _ in range(max_steps):
        response = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=chat_history,
            max_completion_tokens=TOOL_LOOP_MAX_COMPLETION_TOKENS,
            tools=tool_definitions,
            tool_choice="auto"
        )
        message = response.choices[0].message
        
        if not message.tool_calls:
            return chat_history
        chat_history.append(message)
        for tool_call in message.tool_calls:
            result = execute_tool(tool_call)
            chat_history.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result, ensure_ascii=False)
            })
    return chat_history
        

def chat(question: str)-> UEAnswer:
    chat_history.append(
        {
            "role": "user",
            "content": question
        }
    )
    run_tool_loop(chat_history) 
    #GPT生成答案   根据工具信息 GPT添加自然语言进行组织输出
    response = client.chat.completions.parse(
            model=CHAT_MODEL,
            messages=chat_history,
            response_format=UEAnswer
    )
    answer = response.choices[0].message.parsed
    chat_history.append(
        {
            "role":"assistant",
            "content":answer.model_dump_json()
        }
    ) 
    return answer
    
    

def stream_chat(question: str):
    chat_history.append(
            {
                "role": "user",
                "content": question
            }
        )
    run_tool_loop(chat_history)
        
    final_messages = chat_history + [
    {
        "role": "system",
        "content": (
            "请根据前面的对话和工具结果，生成最终答案。"
            "必须只输出 JSON，不要 Markdown，不要代码块，不要额外解释。"
            "JSON 字段必须是 type、reason、solution、code_example。"
            "每个字段保持简洁，code_example 只给一个最小示例。"
        )
    }
    ]
       
    stream = client.chat.completions.create(
        model=CHAT_MODEL,
        messages=final_messages,
        max_completion_tokens=FINAL_MAX_COMPLETION_TOKENS,
        response_format={
          "type": "json_schema",
          "json_schema": {
              "name": "ue_answer",
              "schema": UEAnswer.model_json_schema()
          }
        },
        stream=True
    )
    
    full_answer = ""
    for chunk in stream:
        content = chunk.choices[0].delta.content
        if content:
            full_answer += content
            yield content
    try:
        answer = UEAnswer.model_validate_json(full_answer)
    except Exception as e:
        print("UEAnswer validation failed:")
        print(full_answer)
        raise e              
    chat_history.append(
            {
                "role": "assistant",
                "content": answer.model_dump_json()
            }
        )
    
