from sentence_transformers import CrossEncoder

# Uses a lightweight reranker model
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_results(query: str, candidates: list, top_k: int = 3):
    if not candidates:
        return []

    ranked = [dict(doc) for doc in candidates]
    pairs = [[query, doc["text"][:512]] for doc in ranked]
    scores = reranker.predict(pairs)

    for i, score in enumerate(scores):
        ranked[i]["rerank_score"] = float(score)

    ranked.sort(key=lambda x: x["rerank_score"], reverse=True)
    return ranked[:top_k]
