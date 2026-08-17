from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI()

def get_embeddings(texts, model = "text-embedding-3-large"):
    data = client.embeddings.create(input=texts,model=model).data #data是一个数组 长度根据文本数量
    # print("data length:", len(data))
    # print("first embedding length:", len(data[0].embedding))
    return [x.embedding for x in data]