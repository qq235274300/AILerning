import json
import time
from Agent.patcher import propose_patch
from Agent.planner import analyze_request
from Agent.collector import collect_context
from Agent.searcher import search_knowledge
from Agent.writer import generate_suggestion
from Agent.reviewer import review_answer
from Agent.schemas import CollectedContext

def timed_step(name: str, func, *args, **kwargs):
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed_seconds = round(time.perf_counter() - start, 3)
    print(f"Agent step {name} took {elapsed_seconds}s")
    return result, elapsed_seconds

def should_propose_patch(analysis):
    # Patcher 只负责生成建议，不真实修改文件；必须有本地文件上下文和高风险检查需求才进入。
    return (
        analysis.needs_file_context
        and analysis.needs_review
        and analysis.task_type in {
            "code_analysis",
            "crash_analysis",
            "log_analysis"
        }
    )

def should_collect_context(analysis):
    # 动态路由：只有需要项目文件、代码搜索、日志搜索时才进入 Collector。
    return (
        analysis.needs_file_context
        or analysis.needs_logs_context
        or bool(analysis.file_paths)
    )

def should_search_knowledge(analysis):
    # 动态路由：只有需要 RAG、联网搜索、Crash/日志错误库时才进入 Searcher。
    return (
        analysis.needs_rag_context
        or analysis.needs_web_search
        or analysis.task_type in {
            "crash_analysis",
            "log_analysis"
        }
    )

def should_review_answer(analysis):
    # Reviewer 成本高，只在 Planner 标记高风险任务时启用。
    return analysis.needs_review

def build_final_result(analysis, context, draft, review, timings, patch_suggestion=None):
    final_answer = (
        review.final_answer
        if review is not None
        else draft.answer
    )

    return {
        "analysis": analysis.model_dump(),
        "context": context.model_dump(),
        "draft": draft.model_dump(),
        "patch_suggestion": (
            patch_suggestion.model_dump()
            if patch_suggestion is not None
            else None
        ),
        "review": review.model_dump() if review is not None else None,
        "final_answer": final_answer,
        "timings": timings
    }

def run_agent(question: str):
    #llm模型根据用户模型推理
    total_start = time.perf_counter()
    timings = {}
    analysis, timings["planner"] = timed_step(
        "planner",
        analyze_request,
        question
    )
    
    context = CollectedContext()

    if should_collect_context(analysis):
        context, timings["collector"] = timed_step(
            "collector",
            collect_context,
            question=question,
            analysis=analysis
        )
    else:
        timings["collector"] = 0
        print("Agent step collector skipped")

    if should_search_knowledge(analysis):
        context, timings["searcher"] = timed_step(
            "searcher",
            search_knowledge,
            question=question,
            analysis=analysis,
            context=context
        )
    else:
        timings["searcher"] = 0
        print("Agent step searcher skipped")

    draft, timings["writer"] = timed_step(
        "writer",
        generate_suggestion,
        question=question,
        analysis=analysis,
        context=context
    )

    patch_suggestion = None

    if should_propose_patch(analysis):
        patch_suggestion, timings["patcher"] = timed_step(
            "patcher",
            propose_patch,
            question=question,
            analysis=analysis,
            context=context,
            draft=draft
        )
    else:
        timings["patcher"] = 0
        print("Agent step patcher skipped")

    review = None

    if should_review_answer(analysis):
        review, timings["reviewer"] = timed_step(
            "reviewer",
            review_answer,
            question=question,
            analysis=analysis,
            context=context,
            draft=draft,
            patch_suggestion=patch_suggestion
        )
    else:
        timings["reviewer"] = 0
        print("Agent step reviewer skipped")

    timings["total"] = round(time.perf_counter() - total_start, 3)
    print(f"Agent total took {timings['total']}s")

    return build_final_result(
        analysis=analysis,
        context=context,
        draft=draft,
        review=review,
        timings=timings,
        patch_suggestion=patch_suggestion
    )


def stream_event(event: str, data, elapsed_seconds=None):
    payload = {
        "event": event,
        "data": data
    }
    if elapsed_seconds is not None:
        payload["elapsed_seconds"] = elapsed_seconds

    return json.dumps(
        payload,
        ensure_ascii=False
    ) + "\n"


def run_agent_stream(question: str):
    # Agent 阶段流式输出：让前端能看到 Planner / Collector / Searcher / Writer / Reviewer 的执行进度。
    total_start = time.perf_counter()
    timings = {}
    yield stream_event("planner_start", {})

    analysis, timings["planner"] = timed_step(
        "planner",
        analyze_request,
        question
    )

    yield stream_event(
        "planner_done",
        analysis.model_dump(),
        timings["planner"]
    )

    context = CollectedContext()

    if should_collect_context(analysis):
        yield stream_event("collector_start", {})

        context, timings["collector"] = timed_step(
            "collector",
            collect_context,
            question=question,
            analysis=analysis
        )

        yield stream_event(
            "collector_done",
            context.model_dump(),
            timings["collector"]
        )
    else:
        timings["collector"] = 0
        print("Agent step collector skipped")
        yield stream_event("collector_skipped", {}, 0)

    if should_search_knowledge(analysis):
        yield stream_event("searcher_start", {})

        context, timings["searcher"] = timed_step(
            "searcher",
            search_knowledge,
            question=question,
            analysis=analysis,
            context=context
        )

        yield stream_event(
            "searcher_done",
            context.model_dump(),
            timings["searcher"]
        )
    else:
        timings["searcher"] = 0
        print("Agent step searcher skipped")
        yield stream_event("searcher_skipped", {}, 0)

    yield stream_event("writer_start", {})

    draft, timings["writer"] = timed_step(
        "writer",
        generate_suggestion,
        question=question,
        analysis=analysis,
        context=context
    )

    yield stream_event(
        "writer_done",
        draft.model_dump(),
        timings["writer"]
    )
    
    patch_suggestion = None

    if should_propose_patch(analysis):
        yield stream_event("patcher_start", {})
        patch_suggestion, timings["patcher"] = timed_step(
            "patcher",
            propose_patch,
            question=question,
            analysis=analysis,
            context=context,
            draft=draft
        )
        yield stream_event(
            "patcher_done",
            patch_suggestion.model_dump(),
            timings["patcher"]
        )
    else:
        timings["patcher"] = 0
        print("Agent step patcher skipped")
        yield stream_event("patcher_skipped", {}, 0)

    review = None
    if should_review_answer(analysis):
        yield stream_event("reviewer_start", {})

        review, timings["reviewer"] = timed_step(
            "reviewer",
            review_answer,
            question=question,
            analysis=analysis,
            context=context,
            draft=draft,
            patch_suggestion=patch_suggestion
        )

        yield stream_event(
            "reviewer_done",
            review.model_dump(),
            timings["reviewer"]
        )
    else:
        timings["reviewer"] = 0
        print("Agent step reviewer skipped")
        yield stream_event("reviewer_skipped", {}, 0)

    timings["total"] = round(time.perf_counter() - total_start, 3)
    print(f"Agent total took {timings['total']}s")

    final_result = build_final_result(
        analysis=analysis,
        context=context,
        draft=draft,
        review=review,
        timings=timings,
        patch_suggestion=patch_suggestion
    )

    yield stream_event(
        "final",
        final_result,
        timings["total"]
    )


if __name__ == "__main__":
    result = run_agent(
        "分析 day-01/RAG/chroma.py 这个文件有什么问题"
    )

    print(result["final_answer"])
