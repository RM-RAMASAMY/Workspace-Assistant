from sentence_transformers import CrossEncoder

# Uses a lightweight reranker model
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_results(query: str, candidates: list, top_k: int = 3):
    if not candidates:
        return []

    # Score on a short excerpt — full chunks are passed through after ranking.
    pairs = [[query, doc["text"][:512]] for doc in candidates]
    scores = reranker.predict(pairs)
    
    for i, score in enumerate(scores):
        candidates[i]["rerank_score"] = float(score)
        
    # Sort descending by rerank score
    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    return candidates[:top_k]
