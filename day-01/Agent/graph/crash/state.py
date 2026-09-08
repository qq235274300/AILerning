from typing import TypedDict

from Agent.crash_analyzer import ErrorSummary
from Agent.schemas import CrashReport


class CrashState(TypedDict, total=False):
    """子图只保存 Crash 所需数据，不直接共享主图的消息历史。"""

    log_path: str
    log_text: str
    read_error: str
    error_summary: ErrorSummary
    knowledge: dict
    report: CrashReport
