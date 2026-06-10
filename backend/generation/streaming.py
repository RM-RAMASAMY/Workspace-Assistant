import re

async def sentence_streamer(llm_token_generator):
    """
    Consumes a token stream and yields complete sentences.
    Useful for streaming TTS.
    """
    sentence_endings = re.compile(r'(?<=[.!?])\s+')
    buffer = ""
    
    async for token in llm_token_generator:
        buffer += token
        
        # Check if we have a sentence boundary
        splits = sentence_endings.split(buffer)
        if len(splits) > 1:
            # Yield all complete sentences
            for sentence in splits[:-1]:
                yield sentence.strip()
            # Keep the incomplete part
            buffer = splits[-1]
            
    if buffer.strip():
        yield buffer.strip()
