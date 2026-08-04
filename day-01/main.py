from fastapi import FastAPI

app = FastAPI() #创建API实例
print("111")
@app.get("/") #127.0.0.1 注册一个接口路由
async def root():
    return {"message" : "Hello FastAPI"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )
#启动python main.py