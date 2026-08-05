from fastapi import FastAPI
from pydantic import BaseModel,ValidationError,EmailStr,Field
from typing import Optional
from datetime import date

#定义用户输入模型
class UserInput(BaseModel):
    name: str
    email: EmailStr #pydanic会自动校验邮箱格式
    query: str
    orderid: Optional[int] = Field(
        None,
        description="5-digit order number(cannot start with 0)",
        ge = 10000,
        le = 99999
    )
    purchase_date: Optional[date] = None
#Creat model instance
# user_input = UserInput(
#     name = "Joe User",
#     email="1024747899@qq.com",
#     query="I Forgot my password"
# )    
# print(user_input)

def validate_user_input(input_data):
    try:
        user_input = UserInput(**input_data)
        print(f"🤓 Vaild User Input Created:")
        print(f"{user_input.model_dump_json(indent=2)}")
        return user_input
    except ValidationError as e:
        print(f"😒 Validation error occurred:")
        for error in e.errors():
            print("  - {error['loc'][0]: {error['msg']}")
        return None
    

# input_data = {
#     "name" : "Joe User",
#     "email":"1024747899@qq.com",
#     "query":"I Forgot my password",
#     "orderid": "12345",
#     "purchase_date": date(2026,8,5) 
# }
#模拟用户输入内容由LLM 整理出json
json_data = '''
{
    "name" : "Joe User",
    "email":"1024747899@qq.com",
    "query":"I Forgot my password",
    "orderid": "12345",
    "purchase_date": "2026-08-05" 
}
'''
input_data = UserInput.model_validate_json(json_data)
print(input_data.model_dump_json(indent=2))
# user_input = validate_user_input(input_data)

exit()    

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