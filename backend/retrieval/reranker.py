from sentence_transformers import CrossEncoder

# Uses a lightweight reranker model
reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank_results(query: str, candidates: list, top_k: int = 5):
    if not candidates:
        return []
        
    pairs = [[query, doc["text"]] for doc in candidates]
    scores = reranker.predict(pairs)
    
    for i, score in enumerate(scores):
        candidates[i]["rerank_score"] = float(score)
        
    # Sort descending by rerank score
    candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    return candidates[:top_k]
