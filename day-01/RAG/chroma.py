import chromadb
from .DBembedding import get_embeddings
class ChromaDB:
    
    def __init__(self):
        client = chromadb.PersistentClient(path="./chroma_db")
        self.collection = client.get_or_create_collection("ue_book")
        
    def add(self,documents,embeddings):
        self.collection.add(
            documents=[
                document["page_content"]
                for document in documents
            ],
            metadatas=[
                document["metadata"]
                for document in documents
            ],
            embeddings=embeddings,
            ids=[
                f"id_{i}"
                for i in range(len(documents))
            ]
        )
    def search(self,query,top_k = 3):
        query_embedding = get_embeddings([query])
        return self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
