from Agent.schemas import RequestAnalysis,CollectedContext
from RAG.retriever import search_ue_docs
from tools import search_ue_error
from Agent.web_searcher import search_web

def search_knowledge(question: str, analysis: RequestAnalysis, context: CollectedContext) -> CollectedContext:
    if analysis.needs_rag_context:
        print(f"Tool call: search_ue_docs({question})")
        docs = search_ue_docs(question)
        context.docs.extend(docs)
    if analysis.needs_web_search:
        print("Tool call: search_web()")
        web_result = search_web(question)
        context.web_results.append(web_result)
    if analysis.task_type in {
        "crash_analysis",
        "log_analysis"
    }:
        error_query = question
        if context.logs:
            error_query = context.logs[0].get("text", question)
        print(f"Tool call: search_ue_error({error_query})")
        ue_error = search_ue_error(error_query)
        context.ue_errors.append(ue_error)
    if not analysis.needs_rag_context and analysis.task_type not in {
    "crash_analysis",
    "log_analysis"
    }:
        print("Searcher: no RAG/error tools called")
    return context