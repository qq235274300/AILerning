from dotenv import load_dotenv
from openai import OpenAI
from models import UEAnswer
from prompt import SYSTEM_PROMPT
from tools import search_ue_error
from tool_definitions import tool_definitions
import json

load_dotenv()
client = OpenAI()


def execute_tool(tool_call):
    if tool_call.function.name == "search_ue_error":
        args = json.loads(
            tool_call.function.arguments
        )
        result = search_ue_error(
            args["error_message"]
        )
        return result
    return None

chat_history = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

def chat(question: str)-> UEAnswer:
    chat_history.append(
        {
            "role": "user",
            "content": question
        }
    )
    #判断是否调用工具
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=chat_history,
        temperature=0.2,
        max_tokens=800,
        tools=tool_definitions,
        tool_choice="auto"
    )
    message = response.choices[0].message
    # 保存assistant tool_call消息
    if message.tool_calls:
        print("🚀 GPT decided to call tool!")
        chat_history.append(message)
        for too_call in message.tool_calls:
            print("Tool name:")
            print(too_call.function.name)
            print("Arguments:")
            print(too_call.function.arguments)
            result = execute_tool(too_call)          
            chat_history.append(
                {
                    "role": "tool",
                    "tool_call_id":too_call.id,
                    "content": json.dumps(result)
                }
            ) 
        #GPT生成答案   根据工具信息 GPT添加自然语言进行组织输出
        response = client.chat.completions.parse(
             model="gpt-4o",
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
    
    else:
        #无需工具直接结构化输出
        response = client.chat.completions.parse(
                     model="gpt-4o",
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
    #先判断是否调用工具
    response = client.chat.completions.create(
          model="gpt-5.5",
          messages=chat_history,
          max_completion_tokens=800,
          tools=tool_definitions,
          tool_choice="auto"
      )
    message = response.choices[0].message
     # 2. 如果 GPT 决定调用工具，执行工具并写入历史
    if message.tool_calls:
        print("GPT decided to call tool in stream_chat!")

        chat_history.append(message)

        for tool_call in message.tool_calls:
            print("Tool name:")
            print(tool_call.function.name)
            print("Arguments:")
            print(tool_call.function.arguments)

            result = execute_tool(tool_call)

            chat_history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False)
                }
            )
        
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
        model="gpt-5.5",
        messages=final_messages,
        max_completion_tokens=3000,
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
    
