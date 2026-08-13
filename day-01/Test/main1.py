from fastapi import FastAPI
from pydantic import BaseModel,ValidationError,EmailStr,Field
from typing import Optional,List,Literal
from datetime import date
from dotenv import load_dotenv
import json
import openai


load_dotenv()
client = openai.OpenAI()

# models = client.models.list()
# for m in models:
#     print(m.id)

json_data = '''
{
    "name" : "Joe User",
    "email":"1024747899@qq.com",
    "query":"I Forgot my password",
    "orderid": null,
    "purchase_date": null 
}
'''

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
    
user_input = UserInput.model_validate_json(json_data)

class User_Query(UserInput):
    priority: str = Field(
        ...,description="Priority level : low, medium, high" #... 表示这个字段必须填写
    )
    category: Literal[
        'refund_request','information_request','other'
    ] = Field(...,description="Query category")
    is_complaint: bool = Field(...,description="Whether this is complaint")
    tags: List[str] = Field(...,description="Relevant keyword tags")

#promot 希望LLM回答的格式
example_response_structure = f"""{{
     name = "Joe User",
     email="1024747899@qq.com",
     query="I Forgot my password",
     orderid=12345,
     purchase_date="2026-08-05",
     priority="medium",
     category="refund_request",
     is_complaint=Ture,
     tags=["monitor","support","exchange"]    
}}
"""

prompt = f"""
Please analyze this user query\n {user_input.model_dump_json(indent=2)}:

Return your analysis as as JSON object matching this exact structure
and data types:
{example_response_structure}

Respond Only with valid JSON. Do not include any explanations or
other text or formatting before or after the JSON object.
"""
#校验用户输入 合成prompt
# print(prompt)

def call_llm(prompt,model = "gpt-5.4"):
    response = client.chat.completions.create(
        model=model,
        messages=[{"role":"user","content":prompt}]
    )
    return response.choices[0].message.content

def validate_with_mode(pydantic_model,llm_response):
    try:
        validated_data = pydantic_model.model_validate_json(llm_response)
        print("data validation successful!")
        print(validated_data.model_dump_json(indent=2))
        return validated_data,None
    except ValidationError as e:
        print(f"error validating data: {e}")
        error_message= (
            f"This response generated a validation error: {e}."
        )
        return None,error_message

# response_content = call_llm(prompt)
# valid_response,validation_error = validate_with_mode(User_Query,response_content)

# Function to create a retry prompt with error feedback
def create_retry_prompt(
    original_prompt, original_response, error_message
):
    retry_prompt = f"""
This is a request to fix an error in the structure of an llm_response.
Here is the original request:

<original_prompt>
{original_prompt}
</original_prompt>


Here is the original llm_response:

<llm_response>
{original_response}
</llm_response>


This response generated an error:

<error_message>
{error_message}
</error_message>


Compare the error message and the llm_response and identify what
needs to be fixed or removed in the llm_response to resolve this error.


Respond ONLY with valid JSON. Do not include any explanations or
other text or formatting before or after the JSON string.
"""

    return retry_prompt    

# retry_prompt = create_retry_prompt(prompt,response_content,validation_error)
# response_retry_content = call_llm(retry_prompt)
# valid_retry_response,validation_retry_error = validate_with_mode(User_Query,response_retry_content)

def validate_llm_response(
    prompt, data_model, n_retry=5, model="gpt-5.4"
):
    # Initial LLM call
    response_content = call_llm(prompt, model=model)
    current_prompt = prompt

    # Try to validate with the model
    # attempt: 0=initial, 1=first retry, ...
    for attempt in range(n_retry + 1):

        validated_data, validation_error = validate_with_mode(
            data_model, response_content
        )

        if validation_error:
            if attempt < n_retry:
                print(f"retry {attempt} of {n_retry} failed, trying again...")
            else:
                print(f"Max retries reached. Last error: {validation_error}")
                return None, (
                    f"Max retries reached. Last error: {validation_error}"
                )

            validation_retry_prompt = create_retry_prompt(
                original_prompt=current_prompt,
                original_response=response_content,
                error_message=validation_error
            )

            response_content = call_llm(
                validation_retry_prompt, model=model
            )

            current_prompt = validation_retry_prompt
            continue

        return validated_data, None
    
response_content,error = validate_llm_response(prompt,User_Query)