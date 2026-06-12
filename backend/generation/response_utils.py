import re

REFUSAL_PATTERNS = [
    r"i don'?t have enough information",
    r"i do not have enough information",
    r"i cannot answer",
    r"i can'?t answer",
    r"no information available to answer",
]

# Cross-encoder scores for ms-marco-MiniLM-L-6-v2 are often below 2.5 for valid matches.
MIN_CITATION_RERANK_SCORE = -1.5


def is_insufficient_answer(response: str) -> bool:
    lower = (response or "").lower().strip()
    if len(lower) < 10:
        return True
    return any(re.search(pattern, lower) for pattern in REFUSAL_PATTERNS)


def filter_relevant_chunks(top_chunks: list) -> list:
    if not top_chunks:
        return []
    relevant = [
        chunk for chunk in top_chunks
        if chunk.get("rerank_score", -999) >= MIN_CITATION_RERANK_SCORE
    ]
    return relevant[:3]


def should_attach_citations(
    response: str,
    top_chunks: list,
    intent: str = "factual",
) -> bool:
    if intent == "conversational":
        return False
    if not top_chunks or not (response or "").strip():
        return False
    if is_insufficient_answer(response):
        return False
    top_score = top_chunks[0].get("rerank_score", -999)
    if top_score < MIN_CITATION_RERANK_SCORE:
        return False
    return bool(filter_relevant_chunks(top_chunks))


def build_citation_payload(top_chunks: list) -> list:
    citations = []
    for chunk in filter_relevant_chunks(top_chunks):
        metadata = chunk.get("metadata") or {}
        chunk_id = chunk.get("id")
        if not chunk_id:
            continue
        citations.append({
            "id": chunk_id,
            "document_id": metadata.get("document_id"),
            "title": metadata.get("title"),
            "text": chunk["text"],
            "section_title": metadata.get("section_title") or None,
            "chunk_index": metadata.get("chunk_index"),
            "line_start": _as_int(metadata.get("line_start")),
            "line_end": _as_int(metadata.get("line_end")),
            "rerank_score": chunk.get("rerank_score"),
        })
    return citations


def _as_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
