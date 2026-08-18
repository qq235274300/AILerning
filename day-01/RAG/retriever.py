from .chroma import ChromaDB

db = ChromaDB()

def search_ue_docs(query: str, top_k: int =3):
    result = db.search(query,top_k=top_k)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    snippets = []

    for index, content in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None

        snippets.append(
            {
                "content": content,
                "source": metadata.get("source"),
                "page": metadata.get("page"),
                "chunk_index": metadata.get("chunk_index"),
                "distance": distance
            }
        )

    return snippets
