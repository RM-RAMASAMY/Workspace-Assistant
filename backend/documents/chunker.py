import re

def recursive_character_chunker(text, chunk_size=512, chunk_overlap=64):
    """
    Splits text into chunks of maximum `chunk_size` characters (or tokens approximation),
    with an overlap of `chunk_overlap`.
    It tries to split on double newlines, then single newlines, then sentences.
    """
    separators = ["\n\n", "\n", ". ", " "]
    
    def split_text(text, separators):
        if len(text) <= chunk_size:
            return [text]
            
        sep = separators[0]
        for s in separators:
            if s in text:
                sep = s
                break
                
        splits = text.split(sep)
        
        # Merge splits
        good_splits = []
        current_split = ""
        for s in splits:
            if len(current_split) + len(s) + len(sep) <= chunk_size:
                current_split += s + sep
            else:
                if current_split:
                    good_splits.append(current_split.strip())
                current_split = s + sep
        if current_split:
            good_splits.append(current_split.strip())
            
        # Recursive step if any split is still too large
        final_splits = []
        for s in good_splits:
            if len(s) > chunk_size and len(separators) > 1:
                final_splits.extend(split_text(s, separators[1:]))
            else:
                final_splits.append(s)
                
        return final_splits

    chunks = split_text(text, separators)
    
    # Optional: apply overlap (naive approach)
    overlapped_chunks = []
    for i in range(len(chunks)):
        if i == 0:
            overlapped_chunks.append(chunks[i])
        else:
            overlap_text = chunks[i-1][-chunk_overlap:] if len(chunks[i-1]) > chunk_overlap else chunks[i-1]
            overlapped_chunks.append(overlap_text + " " + chunks[i])
            
    return overlapped_chunks
