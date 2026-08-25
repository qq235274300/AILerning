import json

from Agent.planner import analyze_request
from Agent.collector import collect_context
from Agent.searcher import search_knowledge
from Agent.writer import generate_suggestion
from Agent.reviewer import review_answer

def run_agent(question: str):
    #llm模型根据用户模型推理
    analysis = analyze_request(question)
    
    context = collect_context(
        question=question,
        analysis=analysis
    )

    context = search_knowledge(
        question=question,
        analysis=analysis,
        context=context
    )

    draft = generate_suggestion(
        question=question,
        analysis=analysis,
        context=context
    )

    review = review_answer(
        question=question,
        analysis=analysis,
        context=context,
        draft=draft
    )

    return {
        "analysis": analysis.model_dump(),
        "context": context.model_dump(),
        "draft": draft.model_dump(),
        "review": review.model_dump(),
        "final_answer": review.final_answer
    }


def stream_event(event: str, data):
    return json.dumps(
        {
            "event": event,
            "data": data
        },
        ensure_ascii=False
    ) + "\n"


def run_agent_stream(question: str):
    # Agent 阶段流式输出：让前端能看到 Planner / Collector / Searcher / Writer / Reviewer 的执行进度。
    yield stream_event("planner_start", {})

    analysis = analyze_request(question)

    yield stream_event(
        "planner_done",
        analysis.model_dump()
    )

    yield stream_event("collector_start", {})

    context = collect_context(
        question=question,
        analysis=analysis
    )

    yield stream_event(
        "collector_done",
        context.model_dump()
    )

    yield stream_event("searcher_start", {})

    context = search_knowledge(
        question=question,
        analysis=analysis,
        context=context
    )

    yield stream_event(
        "searcher_done",
        context.model_dump()
    )

    yield stream_event("writer_start", {})

    draft = generate_suggestion(
        question=question,
        analysis=analysis,
        context=context
    )

    yield stream_event(
        "writer_done",
        draft.model_dump()
    )

    yield stream_event("reviewer_start", {})

    review = review_answer(
        question=question,
        analysis=analysis,
        context=context,
        draft=draft
    )

    yield stream_event(
        "reviewer_done",
        review.model_dump()
    )

    yield stream_event(
        "final",
        {
            "analysis": analysis.model_dump(),
            "context": context.model_dump(),
            "draft": draft.model_dump(),
            "review": review.model_dump(),
            "final_answer": review.final_answer
        }
    )


if __name__ == "__main__":
    result = run_agent(
        "分析 day-01/RAG/chroma.py 这个文件有什么问题"
    )

    print(result["final_answer"])
