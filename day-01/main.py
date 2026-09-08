from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from LLM import chat,stream_chat
from Agent.graph.crash.workflow import crash_graph
from Agent.graph.service import (
    run_agent_graph,
    run_agent_graph_stream,
    resume_agent_graph_stream,
)
from models import (
    AgentRequest,
    ChatRequest,
    CrashRequest,
    PatchApprovalRequest,
)

# cd /d D:\Me\VSCodeProjects\day-01
# python -m RAG.build_DB
# cd /d D:\Me\VSCodeProjects
# rmdir /s /q chroma_db

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat_api(req: ChatRequest):

    answer = chat(req.question)

    return {
        "reason": answer.reason,
        "solution": answer.solution,
        "code_example": answer.code_example
    }

@app.post("/chat/stream")
async def chat_stream(req: ChatRequest):

    return StreamingResponse(
        stream_chat(req.question),
        media_type="application/json"
    )
    
# 专用接口直接复用子图，不再维护第二套 Crash 调度。
@app.post("/crash")
def crash_api(req: CrashRequest):
    return crash_graph.invoke({"log_path": req.path})["report"]

# 旧 URL 只做兼容别名，两种地址调用的是同一个处理函数。
@app.post("/agent/graph", deprecated=True)
@app.post("/agent")
def agent_graph_api(req: AgentRequest):
    """
    LangGraph 同步接口。

    等待整张图执行完成后，一次性返回最终结果。
    """

    return run_agent_graph(
        req.question,
        req.thread_id
    )
    
@app.post("/agent/graph/stream", deprecated=True)
@app.post("/agent/stream")
def agent_graph_stream_api(req: AgentRequest):
    """
    LangGraph 节点级流式接口。
    """

    return StreamingResponse(
        run_agent_graph_stream(
            req.question,
            req.thread_id
        ),
        media_type="application/x-ndjson"
    )

#分析 day-01/TestLogs/buggy_texture_loader.py，并生成 Patch 建议
@app.post("/agent/graph/resume", deprecated=True)
@app.post("/agent/resume")
def agent_graph_resume_api(
    req: PatchApprovalRequest
):
    return StreamingResponse(
        resume_agent_graph_stream(
            thread_id=req.thread_id,
            decision=req.decision,
            feedback=req.feedback
        ),
        media_type="application/x-ndjson"
    )

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
