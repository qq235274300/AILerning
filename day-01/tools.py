from pathlib import Path

#resolve绝对路径
PROJECT_ROOT = Path(__file__).resolve().parents[1]

def resolve_safe_path(path: str)-> Path:
    target = (PROJECT_ROOT / path).resolve()
    if not str(target).startswith(str(PROJECT_ROOT)):
        raise ValueError("Path is outside project root")
    return target
#都单一文件
def read_file(path: str):
    target = resolve_safe_path(path)
    if not target.is_file():
        return {"error": f"File not found: {path}"}
    return {
        "path": str(target),
        "content": target.read_text(encoding="utf-8",errors="ignore")
    }
#读文件夹内
def list_files(directory: str):
    target = resolve_safe_path(directory)
    if not target.is_dir():
        return {"error": f"Directory not found: {directory}"}
    return {
        "directory": str(target),
        "files": [
            str(path.relative_to(PROJECT_ROOT))
            for path in target.iterdir()
        ]
    }
    
def search_code(keyword:str , directory: str = "day-01"):
    target = resolve_safe_path(directory)
    matches = []
    skip_dirs = {".git", ".venv", "__pycache__", "chroma_db"}
    for path in target.rglob("*"):
        if any(part in skip_dirs for part in path.parts):
            continue
        if not path.is_file():
            continue
        if path.suffix.lower() in {".pyc",".pdf",".png",".jpg"}:
            continue
        text = path.read_text(encoding="utf-8",errors="ignore")
        
        for line_number, line in enumerate(text.splitlines(),start = 1):
            if keyword.lower() in line.lower():
                matches.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "line": line_number,
                    "text": line.strip()
                })
    return matches[:50]

def search_logs(keyword:str , directory: str = "."):
    target = resolve_safe_path(directory)
    matches = []
    for path in target.rglob("*.log"):
        text = path.read_text(encoding="utf-8",errors="ignore")
        
        for line_number, line in enumerate(text.splitlines(),start = 1):
            if keyword.lower() in line.lower():
                matches.append({
                    "path": str(path.relative_to(PROJECT_ROOT)),
                    "line": line_number,
                    "text": line.strip()
                })
    return matches[:50] 

ue_error_db = [
    {
        "error": "Accessed None trying to read property",

        "reason":
        "The object reference is nullptr. The UObject or variable has not been initialized.",

        "solution":
        """
        1. Check whether the object is valid.
        2. Use IsValid() before accessing UObject.
        3. Check BeginPlay initialization order.
        4. Verify GameInstance or Actor reference.
        """
    },


    {
        "error": "Unable to find package",

        "reason":
        "Unreal Engine cannot locate the referenced asset or package.",

        "solution":
        """
        1. Check asset path.
        2. Verify the package exists.
        3. Check plugin mount point.
        4. Rebuild project.
"""
    }
]


def search_ue_error(error_message: str):

    for item in ue_error_db:

        if item["error"].lower() in error_message.lower():

            return item


    return {
        "error": error_message,
        "reason": "No matching UE error found.",
        "solution": "Please provide more information."
    }

def read_log(path: str):
    """
    读取日志文件，只用于 Crash 分析，不修改任何文件。
    """
    target = resolve_safe_path(path)
    if not target.is_file():
        return {
            "error": f"Log file not found: {path}"
        }
    text = target.read_text(
        encoding="utf-8",
        errors="ignore"
    )
    #截取最后两万字
    return {
        "path": str(target.relative_to(PROJECT_ROOT)),
        "content": text[-20000:]
    }