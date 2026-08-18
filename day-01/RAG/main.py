
from DBembedding import get_embeddings
from chroma import ChromaDB

db = ChromaDB()

# Retriever 检索 DB库
result = db.search("什么时候改继承自UObject类")

print(result)

