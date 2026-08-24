from openai_client import CHAT_MODEL, client


def search_web(query: str):
    response = client.responses.create(
        model=CHAT_MODEL,
        tools=[
            {
                "type": "web_search"
            }
        ],
        input=(
            "请联网搜索并回答下面的问题。"
            "如果涉及候选人、天气、新闻、政策、版本、价格等实时信息，"
            "请优先基于搜索结果回答，并尽量说明信息来源。\n\n"
            f"问题：{query}"
        )
    )

    return {
        "query": query,
        "answer": response.output_text
    }
