from pydantic import BaseModel,ValidationError,EmailStr,Field,field_validator
from pydantic_ai import Agent
from typing import Optional,List,Literal
from openai import OpenAI
import instructor #LLM包装器
from dotenv import load_dotenv
from datetime import date,datetime
import json
import nest_asyncio
from fastapi import FastAPI

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
# print(type(valid_response))
# print(valid_response.model_dump_json(indent=2))

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
        "purchase_date": "2026-08-06",
        "email": "1024747899@qq.com"
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
#知识库检索 每个单词比对获得分数
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

def check_order_status(args: CheckOrderStatusArgs):
    """Simulate checking the status of a customer's order by
    order_id and email."""
    order = order_db.get(args.order_id)
    if not order:
        return {
            "order_id": args.order_id,
            "status": "not found",
            "estimated_delivery": None,
            "note": "order_id not found"
        }
    if args.email.lower() != order.get("email", "").lower():
        return {
            "order_id": args.order_id,
            "status": order["status"],
            "estimated_delivery": order["estimated_delivery"],
            "note": "order_id found but email mismatch"
        }
    return {
        "order_id": args.order_id,
        "status": order["status"],
        "estimated_delivery": order["estimated_delivery"],
        "note": "order_id and email match"
    }

#pass to LLM
tool_definitions = [
    {
        "type": "function",
        "function": {
            "name": "lookup_faq_answer",
            "description": "Look up an FAQ answer by matching tags to FAQ DATABASE.",
            "parameters": FAQLookupArgs.model_json_schema()
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_order_status",
            "description": "Check the status of a customer's order.",
            "parameters": CheckOrderStatusArgs.model_json_schema()
        }
    }
]

class OrderDetails(BaseModel):
    status: str
    estimated_delivery: str
    note: str

class SupportTicket(User_Query):
    recommended_next_action: Literal[
        'escalate_to_agent','send_faq_response',
        'send_order_statuss','no_action_needed'
    ] = Field(
        ...,description="LLM's recommended next action for support"
    )
    order_details: Optional[OrderDetails] = Field(
        None, description="Order details if action is send_order_status"
    )
    faq_response: Optional[str] = Field(
        None,description="FAQ response if action is send_faq_response"
    )
    creation_date: datetime = Field(
        ...,description="Date and time the ticket was created"
    )

client = OpenAI()
def decide_next_action_with_tools(user_query: User_Query):
    support_ticket_schema = json.dumps(
        SupportTicket.model_json_schema(),indent=2
    )
    system_prompt = f"""
    You are a helpful customer support agent. Your job is to
    determine what support action should be taken for the customer,
    based on the customer query and the expected fields in the
    SupportTicket schema below. If more information on a particular
    order_id or FAQ response would be helpful in responding to the
    user query and can be obtained by calling a tool, call the
    appropriate tool to get that information. If an order_id is
    present in the query, always look up the order status to get
    more information on the order.

    Here is the JSON schema for the SupportTicket model you must
    use as context for what information is expected:
    {support_ticket_schema}
    """    
    messages = [
        {"role": "system","content": system_prompt},
        {"role": "user","content": str(user_query.model_dump())}
    ]
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools = tool_definitions,
        tool_choice="auto"
    )
    message = response.choices[0].message
    tool_calls = getattr(message,"tool_calls",None)
    return message, tool_calls, messages

message, tool_calls, messages = decide_next_action_with_tools(
    valid_response
)   
# print("LLM message:\n", json.dumps(message.model_dump(),indent=2))
# print(
#     "\nTool calls:\n",
#     json.dumps([call.model_dump() for call in tool_calls],indent=2)
# )

def get_tool_outputs(tool_calls):
    tool_outputs = []

    if tool_calls:
        for tool_call in tool_calls:

            if tool_call.function.name == "lookup_faq_answer":
                print("Agent requested a call to the Lookup FAQ tool...")

                args = FAQLookupArgs.model_validate_json(
                    tool_call.function.arguments
                )

                result = lookup_faq_answer(args)

                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })

                print(f"Lookup FAQ tool returned {result}")

            elif tool_call.function.name == "check_order_status":
                print("Agent requested a call to Check Order Status tool...")

                args = CheckOrderStatusArgs.model_validate_json(
                    tool_call.function.arguments
                )

                result = check_order_status(args)

                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": result
                })

                print(f"Check Order Status tool returned {result}")

    return tool_outputs

# Stage 2: Gather any needed tool outputs and generate a support
# ticket (run this after inspecting above)

# tool_outputs = get_tool_outputs(tool_calls)
# print("Tool outputs:\n", json.dumps(tool_outputs, indent=2))

# Create the OpenAI client with Instructor
openai_client = instructor.from_openai(
    OpenAI()
)

def generate_structured_support_ticket(
    customer_query: User_Query,
    message,
    tool_outputs: list
) -> SupportTicket:

    tool_results_str = "\n".join([
        f"Tool: {out['tool_call_id']} Output: {json.dumps(out['output'])}"
        for out in tool_outputs
    ]) if tool_outputs else "No tool calls were made."

    # Concatenate prompt parts into a single string
    prompt = f"""
        You are a support agent. Use all information below to
        generate a support ticket as a validated Pydantic model.
        Customer query:{customer_query.model_dump_json(indent=2)}
        LLM message:{str(message.content)}
        Tool results:{tool_results_str}
    """
    # Create the message with structured output
    support_ticket = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_model=SupportTicket
    )

    support_ticket.creation_date = datetime.now()
    return support_ticket

# support_ticket = generate_structured_support_ticket(valid_response,message,tool_outputs)
# print(support_ticket.model_dump_json(indent=2))

#Test
test_json = '''
    {
    "name": "Joe User",
    "email": "joe@example.com",
    "query": "How can I delete my account",
    "order_id": "QWE-34567",
    "purchase_date": null
    }
    '''
#测试获得support ticket
# valid_test_json = validate_user_input(test_json).model_dump_json()
# test_query= create_customer_query(valid_test_json)
# message,tool_calls,messages = decide_next_action_with_tools(test_query)
# tool_outputs = get_tool_outputs(tool_calls)
# support_ticket = generate_structured_support_ticket(
#     test_query,message,tool_outputs
# )
# print(support_ticket.model_dump_json(indent=2))

class ChatRequest(BaseModel):
    question: str

app = FastAPI()

# client_messages = [
#     {"role": "system","content": "You are an Unreal Engine C++ expert with 10 years of experience."},
#     {"role": "user","content": ChatRequest.question},
#     {"role": "assistant","content": ""}
# ]

class UEAnswer(BaseModel):
    reason: str
    solution: str
    code_example: str

chat_history = [
    {
        "role": "system",
        "content": "You are an Unreal Engine C++ expert with 10 years of experience."
    }
]
   
@app.post("/chat")
async def chat(req: ChatRequest):
    chat_history.append(
        {
            "role": "user",
            "content": req.question
        }
    )
    response = client.chat.completions.parse(
        model="gpt-4o",
        messages=chat_history,
        response_format=UEAnswer     
    )
    answer = response.choices[0].message.parsed
    chat_history.append(
        {
            "role": "assistant",
            "content": answer.solution
        }
    )
    return {
        "reason": answer.reason,
        "solution": answer.solution,
        "code_example": answer.code_example
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000
    )

