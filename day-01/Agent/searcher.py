from Agent.schemas import RequestAnalysis,CollectedContext
from RAG.retriever import search_ue_docs
from tools import search_ue_error

def search_knowledge(question: str, analysis: RequestAnalysis, context: CollectedContext) -> CollectedContext:
    if analysis.needs_rag_context:
        docs = search_ue_docs(question)
        context.docs.extend(docs)
    if analysis.task_type in {
        "crash_analysis",
        "log_analysis"
    }:
        error_query = question
        if context.logs:
            error_query = context.logs[0].get("text", question)
        ue_error = search_ue_error(error_query)
        context.ue_errors.extend(ue_error)
    return context