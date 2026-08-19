import chromadb
import hashlib
from .DBembedding import get_embeddings

def make_document_id(document, index):
    source = document["metadata"].get("source", "unknown")
    page = document["metadata"].get("page", "unknown")
    chunk_index = document["metadata"].get("chunk_index", index)

    raw_id = f"{source}:{page}:{chunk_index}"

    return hashlib.md5(raw_id.encode("utf-8")).hexdigest()

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
               make_document_id(document, i)
               for i, document in enumerate(documents)
            ]
        )
    def search(self,query,top_k = 3):
        query_embedding = get_embeddings([query])
        return self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k
        )
