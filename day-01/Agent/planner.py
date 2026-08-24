from openai_client import CHAT_MODEL, client
from Agent.schemas import RequestAnalysis

# analyze_request("分析 day-01/RAG/chroma.py") 调用尝试
def analyze_request(question: str)-> RequestAnalysis:
    response = client.chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {
              "role": "system",
              "content": (
                    "你是 Planner，只判断用户问题类型和需要哪些上下文，"
                    "不要回答用户问题。"
                    "如果用户提到具体文件路径，把它放入 file_paths。"
                    "如果需要搜索代码、日志或知识库，给出 search_keywords。"
                )  
            },
            {
                "role": "user",
                "content": question
            }
        ],
        response_format=RequestAnalysis
    )
    return response.choices[0].message.parsed
