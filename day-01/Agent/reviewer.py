from openai_client import CHAT_MODEL, client
from Agent.schemas import (
    RequestAnalysis,
    CollectedContext,
    DraftAnswer,
    PatchSuggestion,
    ReviewResult
)

def review_answer(
    question: str,
    analysis: RequestAnalysis,
    context: CollectedContext,
    draft: DraftAnswer,
    patch_suggestion: PatchSuggestion | None = None
) -> ReviewResult:
    # Patcher 是可选阶段；没有 patch 时传 None，让 Reviewer 只检查普通答案。
    patch_text = (
        patch_suggestion.model_dump_json(indent=2)
        if patch_suggestion is not None
        else "None"
    )

    response = client.chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是 Reviewer，负责检查 Writer 的答案质量。"
                    "检查是否基于上下文、是否引用来源、是否有未支持的结论、是否遗漏风险。"
                    "如果存在 patch 建议，还要检查 patch 是否只作为建议、是否说明风险、是否需要人工确认。"
                    "如果问题是实时信息问题，检查答案是否使用了 web_results。"
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
                    f"Writer 初稿:\n{draft.model_dump_json(indent=2)}\n\n"
                    f"Patch 建议:\n{patch_text}"
                )
            }
        ],
        response_format=ReviewResult
    )

    return response.choices[0].message.parsed
