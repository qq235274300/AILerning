from .chroma import ChromaDB

db = ChromaDB()

def search_ue_docs(query: str, top_k: int =3):
    result = db.search(query,top_k=top_k)
    documents = result.get("documents",[[]])[0]
    return [
        {
            "content": doc
        }
        for doc in documents
    ]
