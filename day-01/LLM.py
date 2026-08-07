from pydantic import BaseModel,ValidationError,EmailStr,Field,field_validator
from pydantic_ai import Agent
from typing import Optional,List,Literal
from openai import OpenAI
import instructor #LLM包装器
from dotenv import load_dotenv
from datetime import date,datetime
import json
import nest_asyncio

load_dotenv()
nest_asyncio.apply()

class UserInput(BaseModel):
    name: str = Field(...,description="User's name")
    email: EmailStr = Field(...,description="User's email address")#pydanic会自动校验邮箱格式
    query: str= Field(...,description="User's query")
    order_id: Optional[str] = Field(
        None,
        description="Order ID if available(format: ABC-12345)"
    )
    @field_validator("order_id")
    def validate_order_id(cls,order_id):
        import re
        if order_id is None:
            return order_id
        pattern = r"^[A-Z]{3}-\d{5}$"
        if not re.match(pattern,order_id):
            raise ValueError(
                "order_id must be in format ABC-12345 "
                "(3 uppercase letters, dash, 5digits)"
            )
    purchase_date: Optional[date] = None

class User_Query(UserInput):
    priority: str = Field(
        ...,description="Priority level : low, medium, high" #... 表示这个字段必须填写
    )
    category: Literal[
        'refund_request','information_request','other'
    ] = Field(...,description="Query category")
    is_complaint: bool = Field(...,description="Whether this is complaint")
    tags: List[str] = Field(...,description="Relevant keyword tags")
    
def validate_user_input(user_json: str):
    """Validate user input from a JSON string and return a UserInput instance if
    valid."""
    try:
        user_input = (
            UserInput.model_validate_json(user_json)
        )
        print("user input validated...")
        return user_input
    except Exception as e:
        print(f" Unexpected error: {e}")
        return None
    
def create_customer_query(valid_user_json: str) -> User_Query:
    customer_query_agent = Agent(
        model="openai:gpt-4o",
        output_type=User_Query,
    )
    response = customer_query_agent.run_sync(valid_user_json)
    print("CustomerQuery generated...")
    return response.output

user_input_json = '''
{
    "name" : "Joe User",
    "email":"1024747899@qq.com",
    "query":"When can I expect delivery of the headphones I ordered?",
    "orderid": "ABC-12345",
    "purchase_date": "2026-08-06" 
}
'''
#根据用户输入 通过LLM&pydantic 得到希望的结构 
valid_date = validate_user_input(user_input_json).model_dump_json()
valid_response = create_customer_query(valid_date)
print(type(valid_response))
print(valid_response.model_dump_json(indent=2))

#FAQ Lookup tool input
class FAQLookupArgs(BaseModel):
    query: str = Field(...,description="User's query")
    tags: List[str] = Field(...,description="Relevant keyword tags from the customer query")

 #Check Order Status tool input
class CheckOrderStatusArgs(BaseModel):
    order_id: str = Field(
            ...,
            description="Customer's ID (format: ABC-12345)"
        )
    email: EmailStr = Field(...,description="Customer's email address")#pydanic会自动校验邮箱格式
    @field_validator("order_id")
    def validate_order_id(cls,order_id):
        import re
        if order_id is None:
            return order_id
        pattern = r"^[A-Z]{3}-\d{5}$"
        if not re.match(pattern,order_id):
            raise ValueError(
                "order_id must be in format ABC-12345 "
                "(3 uppercase letters, dash, 5digits)"
            )
        return order_id   

# Fake FAQ database as a list of entries with keywords
faq_db = [
    {
        "question": "How can I reset my password?",
        "answer": "To reset your password, click 'Forgot Password' on the login page and follow the instructions sent to your registered email address.",
        "keywords": ["password", "reset", "account"]
    },
    {
        "question": "How long does shipping take?",
        "answer": "Standard shipping takes 3-5 business days. You can track your order status using the tracking number provided in your shipping confirmation email.",
        "keywords": ["shipping", "delivery", "order", "tracking"]
    },
    {
        "question": "How can I return an item?",
        "answer": "You can return any item within 30 days of purchase. Visit your order page, select the item you want to return, and follow the return instructions.",
        "keywords": ["return", "refund", "exchange"]
    },
    {
        "question": "How can I delete my account?",
        "answer": "To delete your account, go to your account settings and select the account deletion option. Please note that this action cannot be undone.",
        "keywords": ["delete", "account", "remove"]
    }
]

order_db = {
    "ABC-12345": {
        "status": "shipped",
        "estimated_delivery": "2025-12-05",
        "purchase_date": "2025-12-01",
        "email": "joe@example.com"
    },
    "XYZ-23456": {
        "status": "processing",
        "estimated_delivery": "2025-12-15",
        "purchase_date": "2025-12-10",
        "email": "sue@example.com"
    },
    "QWE-34567": {
        "status": "delivered",
        "estimated_delivery": "2025-12-20",
        "purchase_date": "2025-12-18",
        "email": "bob@example.com"
    }
}
#知识库检索
def lookup_faq_answer(args: FAQLookupArgs) -> str:
    """Look up an FAQ answer by matching tags and words in query
    to FAQ entry keywords."""
    query_words = set(word.lower() for word in args.query.split())
    tag_set = set(tag.lower() for tag in args.tags)
    best_match = None
    best_score = 0
    for faq in faq_db:
        keywords = set(k.lower() for k in faq["keywords"])
        score = len(keywords & tag_set) + len(keywords & query_words)
        if score > best_score:
            best_score =score
            best_match = faq
    if best_match and best_score > 0:
        return best_match["answer"]
    return "Sorry , I couldn't find an FAQ answer for your question."
    