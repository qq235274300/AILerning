from openai_client import CHAT_MODEL, client
from Agent.schemas import (
    RequestAnalysis,
    CollectedContext,
    DraftAnswer,
    ReviewResult
)

def review_answer(
    question: str,
    analysis: RequestAnalysis,
    context: CollectedContext,
    draft: DraftAnswer
) -> ReviewResult:
    response = client.chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Reviewer，负责检查 Writer 的答案质量。"
                    "检查是否基于上下文、是否引用来源、是否有未支持的结论、是否遗漏风险。"
                    "如果答案可用，passed=true，并输出润色后的 final_answer。"
                    "如果答案有问题，passed=false，列出 issues，并给出修正后的 final_answer。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"用户问题:\n{question}\n\n"
                    f"Planner 分析:\n{analysis.model_dump_json(indent=2)}\n\n"
                    f"上下文:\n{context.model_dump_json(indent=2)}\n\n"
                    f"Writer 初稿:\n{draft.model_dump_json(indent=2)}"
                )
            }
        ],
        response_format=ReviewResult
    )

    return response.choices[0].message.parsed
