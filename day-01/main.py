from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from models import ChatRequest,CrashRequest
from LLM import chat,stream_chat
from Agent.pipeline import run_agent,run_agent_stream
from Agent.crash_analyzer import run_crash_agent

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
    
@app.post("/agent")
async def agent_api(req: ChatRequest):
    result = run_agent(req.question)
    return result

@app.post("/agent/stream")
async def agent_stream_api(req: ChatRequest):
    return StreamingResponse(
        run_agent_stream(req.question),
        media_type="application/x-ndjson"
    )

#检查UE Crash专用流程，Agent使用agent_stream_api
@app.post("/crash")
async def crash_api(req: CrashRequest):
    return run_crash_agent(req.path)

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
