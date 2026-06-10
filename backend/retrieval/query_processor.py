def process_query(transcription: str, history: list):
    # In a full version, we'd call an LLM to rewrite the query based on history
    # For PoC, we return the transcription as-is or do simple heuristics
    
    # Determine intent heuristically or via LLM
    intent = "factual"
    if transcription.lower() in ["hi", "hello", "who are you"]:
        intent = "conversational"
        
    return {
        "rewritten": transcription,
        "variants": [transcription], # Placeholder for multi-query
        "intent": intent
    }
