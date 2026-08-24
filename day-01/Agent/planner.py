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
                    "如果用户询问实时信息、新闻、天气、选举、最新版本、当前价格、政策变化、"
                    "今天/明天/今年这类强时效问题，设置 needs_web_search=true。"
                    "如果问题可以直接回答且不需要本地项目、RAG 或联网信息，则不要开启任何上下文需求。"
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
