def evaluate_response(query: str, response: str, citations: list):
    """
    Dummy evaluator for PoC. In production, this would call an LLM-as-a-judge 
    or a smaller model to score faithfulness and relevance.
    """
    # Simple heuristic: if citations exist, faithfulness score is high
    faithfulness = 0.9 if citations else 0.5
    relevance = 0.85
    citation_accuracy = 1.0 if citations and any(f"[{c['id']}]" in response for c in citations) else 0.0
    
    return {
        "faithfulness": faithfulness,
        "relevance": relevance,
        "citation_accuracy": citation_accuracy
    }
