import chromadb
class ChromaDB:
    
    def __init__(self):
        client = chromadb.Client()
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
    def search(self,embedding,top_k = 3):
        return self.collection.query(
            query_embeddings=[embedding],
            n_results=top_k
        )