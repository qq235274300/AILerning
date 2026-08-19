def rerank(query, snippets, top_k=5):
    sorted_snippets = sorted(
        snippets,
        key=get_distance_for_sort
    )

    return sorted_snippets[:top_k]

def get_distance_for_sort(snippet):
    distance = snippet.get("distance")

    if distance is None:
        return float("inf")

    return distance