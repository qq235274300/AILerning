from openai_client import client, CHAT_MODEL
from Agent.schemas import RequestAnalysis, CollectedContext, DraftAnswer, PatchSuggestion

#用于生成分析代码的patch 目前只是生成patch不直接修改

def propose_patch(
    question: str,
    analysis: RequestAnalysis,
    context: CollectedContext,
    draft: DraftAnswer
) -> PatchSuggestion:
    response = client.chat.completions.parse(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是代码 Patch 建议器。"
                    "你只能生成 patch 建议，不能真实修改文件。"
                    "生成的 patch_diff 只是给人审查的文本，不要声称已经应用到项目。"
                    "必须输出 old_code、new_code、patch_diff、风险和是否需要人工确认。"
                    "如果上下文不足以生成可靠 patch，要明确说明风险，并设置 needs_human_confirm=true。"
                )
            },
            {
                "role": "user",
                "content": (
                    f"用户问题:\n{question}\n\n"
                    f"Planner 分析:\n{analysis.model_dump_json(indent=2)}\n\n"
                    f"已收集上下文:\n{context.model_dump_json(indent=2)}\n\n"
                    f"Writer 草稿:\n{draft.model_dump_json(indent=2)}"
                )
            }
        ],
        response_format=PatchSuggestion
    )

    return response.choices[0].message.parsed
