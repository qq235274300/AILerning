from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

CHAT_MODEL = "gpt-5.5"
TOOL_LOOP_MAX_COMPLETION_TOKENS = 800
FINAL_MAX_COMPLETION_TOKENS = 3000
