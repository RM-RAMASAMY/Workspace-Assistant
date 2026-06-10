from sentence_transformers import SentenceTransformer
from .vector_store import search_vector_store

embedder = SentenceTransformer("all-MiniLM-L6-v2")

def perform_hybrid_search(query: str, access_level: int, top_k: int = 40):
    # For PoC, we will just use the dense search via ChromaDB
    # Full hybrid with BM25 can be implemented by indexing chunks with rank_bm25
    query_embedding = embedder.encode(query).tolist()
    
    results = search_vector_store(query_embedding, access_level, n_results=top_k)
    
    # Restructure ChromaDB results to a list of dicts
    candidates = []
    if results and "ids" in results and results["ids"]:
        ids = results["ids"][0]
        distances = results["distances"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        for i in range(len(ids)):
            candidates.append({
                "id": ids[i],
                "text": documents[i],
                "score": distances[i], # Cosine distance (lower is better, or higher if similarity)
                "metadata": metadatas[i]
            })
            
    return candidates
