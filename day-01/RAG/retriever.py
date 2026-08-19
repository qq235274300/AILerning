from .chroma import ChromaDB
from .reranker import rerank
db = ChromaDB()

#将向量距离转为更直接的得分
def distance_to_score(distance):
    if distance is None:
        return None
    return 1 / (1+ distance)

def search_ue_docs(query: str, recall_k: int =20, final_k: int = 5):
    result = db.search(query,top_k=recall_k)
    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    snippets = []

    for index, content in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        score = distance_to_score(distance)
        if score is not None:
            score = round(score,4)
        snippets.append(
            {
                "content": content,
                "source": metadata.get("source"),
                "page": metadata.get("page"),
                "chunk_index": metadata.get("chunk_index"),
                "distance": distance,
                "score": score
            }
        )
    ranked_snippets = rerank(
        query=query,
        snippets=snippets,
        top_k=final_k
    )

    return ranked_snippets
