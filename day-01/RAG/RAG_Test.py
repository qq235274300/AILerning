from openai import OpenAI
from dotenv import load_dotenv
import numpy as np
from numpy import dot
from numpy.linalg import norm
import re
import json
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb
from chromadb.config import Settings

load_dotenv()

client = OpenAI()


#1）按标点符号分割 可能导致部门句子长度过长 过短
text = """
自然语言处理（NLP），作为计算机科学、人工智能与语言学的交融之地，致力于赋予计算机解析和处理人类语言的能力。在这个领域，机器学习发挥着至关重要的作用。利用多样的算法，机器得以分析、领会乃至创造我们所理解的语言。从机器翻译到情感分析，从自动摘要到实体识别，NLP的应用已遍布各个领域。随着深度学习技术的飞速进步，NLP的精确度与效能均实现了巨大飞跃。如今，部分尖端的NLP系统甚至能够处理复杂的语言理解任务，如问答系统、语音识别和对话系统等。NLP的研究推进不仅优化了人机交流，也对提升机器的自主性和智能水平起到了关键作用。
"""
# 正则表达式匹配中文句子结束的标点符号
sentences = re.split(r'(。|！|？|\.|!|\?)', text)
# 重新组合句子和结尾的标点符号
chunks = [
    sentence + (punctuation if punctuation else '')
    for sentence, punctuation in zip(sentences[::2], sentences[1::2])
]

#2) 按固定字符数切割 语义大概率会乱
def split_by_fixed_char_count(text,count):
    return [text[i:i + count] for i in range(0, len(text), count)]

chunks = split_by_fixed_char_count(text,100)

#3） 滑动窗口 字符量会变大但语义有所增强
def sliding_window_chunks(text, chunk_size, stride):
    return [text[i: i+ chunk_size] for i in range(0, len(text), stride)]
chunks = sliding_window_chunks(text,100,50)

#4) 使用递归的方法来切割字符
splitter = RecursiveCharacterTextSplitter(
    chunk_size =50,
    chunk_overlap = 10,
    length_function = len
)
chunks = splitter.split_text(text)


for i, chunk in enumerate(chunks):
    print(f"块 {i+1}: {len(chunk)}: {chunk}")

#向量检索 redis服务 RDM操作
#向量数据库

#余弦局里 表示向量方向相似度 值越大越相似
def cos_sim(a,b):
    return dot(a,b)/(norm(a)*norm(b))
#欧式距离 越小越相似
def l2(a,b):
    x= np.asarray(a) - np.asarray(b)
    return norm(x)
#知识库 将数据(pdf txt execl..)chunk ,chunk切分方式很多


def get_embeddings(texts, model = "text-embedding-3-large"):
    data = client.embeddings.create(input=texts,model=model).data #data是一个数组 长度根据文本数量
    # print("data length:", len(data))
    # print("first embedding length:", len(data[0].embedding))
    return [x.embedding for x in data]

with open('.josn','r',encoding='uft-8') as f :
    data = [json.loads(line) for line in f]
    
instructions = [entry['instruction'] for entry in data[0:100]]
outputs = [entry['outut'] for entry in data[0:100]]

class MyVectorDCCOnnector:
    def __init__(self,collection_name,embedding_fn):
        chroma_client = chromadb.Client(Settings(allow_reset = True))
        chroma_client.reset()
        self.collection = chroma_client.get_or_create_collection(name = collection_name)
        self.embedding_fn = embedding_fn
        
    def add_documents(self,instructions,outputs):
        embeddings = self.embedding_fn(instructions)
        self.collection.add(
            embeddings= embeddings,
            documents=outputs,
            ids = [f"id{i}" for i in range(len(outputs))]
        )
    
    def search(self, query, top_n):
        results = self.collection.query(
            query_embeddings=self.embedding_fn([query]),
            n_results=top_n
        )
        return results
    
vector_db = MyVectorDCCOnnector("demo",get_embeddings)
vector_db.add_documents(instructions,outputs)
user_query = ""
results = vector_db.search(user_query,2)

for para in results['documents'][0]:
    print(para + "\n")