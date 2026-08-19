
from RAG.chroma import ChromaDB

db = ChromaDB()

# Retriever 检索 DB库
result = db.search("什么时候该继承自UObject类")

print(result)

