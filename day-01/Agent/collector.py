from Agent.schemas import RequestAnalysis,CollectedContext
from tools import read_file,search_code,search_logs

def extract_keyword(question: str)-> str:
    words = question.replace("，", " ").replace("。", " ").split()
    for word in words:
        if len(word) > 2:
            return word
    return question    

def collect_context(question: str, analysis: RequestAnalysis) -> CollectedContext:
    context = CollectedContext()
    for file_path in analysis.file_paths:
        print(f"Tool call: read_file({file_path})")
        context.files.append(
            read_file(file_path)
        )
    if analysis.needs_file_context:
        keywords = analysis.search_keywords or [
            extract_keyword(question)
        ]
        for keyword in keywords:
            print(f"Tool call: search_code(keyword={keyword}, directory=.)")
            code_result = search_code(
                keyword=keyword,
                directory="."
            )
            context.code_snippets.extend(code_result)
    if analysis.needs_logs_context:
        keywords = analysis.search_keywords or [
                    extract_keyword(question)
                ]
        for keyword in keywords:
            print(f"Tool call: search_logs(keyword={keyword}, directory=.)")
            log_result = search_logs(
                keyword=keyword,
                directory="."
            )
            context.logs.extend(log_result)
    if not context.files and not context.code_snippets and not context.logs:
        print("Collector: no file/code/log tools called")
    return context