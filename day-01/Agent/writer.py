from openai_client import CHAT_MODEL, client
from Agent.schemas import RequestAnalysis, CollectedContext, DraftAnswer


# cd /d D:\Me\VSCodeProjects\day-01
# python -m agent.pipeline

def generate_suggestion(
    question: str,
    analysis: RequestAnalysis,
    context: CollectedContext
) -> DraftAnswer:
    response = client.chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Writer，负责基于 Planner 分析和已收集上下文生成技术建议。"
                    "不要声称没有上下文支持的结论。"
                    "如果使用 RAG 文档，尽量引用 source/page。"
                    "如果 context.web_results 中有联网搜索结果，优先基于联网结果回答实时问题。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"用户问题:\n{question}\n\n"
                    f"Planner 分析:\n{analysis.model_dump_json(indent=2)}\n\n"
                    f"收集到的上下文:\n{context.model_dump_json(indent=2)}"
                )
            }
        ],
        response_format=DraftAnswer
    )

    return response.choices[0].message.parsed
