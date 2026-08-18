import chromadb
from .DBembedding import get_embeddings
class ChromaDB:
    
    def __init__(self):
        client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = client.get_or_create_collection("ue_book")
        
    def add(self,chunks,embeddings):
        self.collection.add(
            documents=chunks,
            embeddings=embeddings,
            ids=[
                f"id_{i}"
                for i in range(len(chunks))
            ]
        )
    def search(self,query,top_k = 3):
        query_embedding = get_embeddings([query])
        return self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
