from Agent.planner import analyze_request
from Agent.collector import collect_context
from Agent.searcher import search_knowledge
from Agent.writer import generate_suggestion
from Agent.reviewer import review_answer

def run_agent(question: str):
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


if __name__ == "__main__":
    result = run_agent(
        "分析 day-01/RAG/chroma.py 这个文件有什么问题"
    )

    print(result["final_answer"])