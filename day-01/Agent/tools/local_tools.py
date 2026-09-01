from langchain.tools import tool
from tools import (
    list_files as project_list_files,
    read_file as project_read_file,
    search_code as project_search_code,
    search_logs as project_search_logs,
)

@tool("read_file")
def read_file_tool(path: str) -> dict:
    """
    读取项目内的 UTF-8 文本文件，不修改文件。

    Args:
        path: 相对于项目根目录的文件路径。
    """

    return project_read_file(path)


@tool("list_files")
def list_files_tool(directory: str) -> dict:
    """
    列出项目目录中的文件。

    Args:
        directory: 相对于项目根目录的目录路径。
    """

    return project_list_files(directory)

@tool("search_code")
def search_code_tool(
    keyword: str,
    directory: str = "day-01"
) -> list[dict]:
    """
    在项目源码中搜索关键词。

    Args:
        keyword: 需要搜索的代码关键词。
        directory: 搜索范围，默认为 day-01。
    """

    return project_search_code(
        keyword=keyword,
        directory=directory
    )


@tool("search_logs")
def search_logs_tool(
    keyword: str,
    directory: str = "."
) -> list[dict]:
    """
    在项目日志文件中搜索关键词。

    Args:
        keyword: 需要搜索的日志关键词。
        directory: 日志搜索范围。
    """

    return project_search_logs(
        keyword=keyword,
        directory=directory
    )
    
LOCAL_TOOLS = [
    read_file_tool,
    list_files_tool,
    search_code_tool,
    search_logs_tool
]