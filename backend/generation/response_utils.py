import re

REFUSAL_PATTERNS = [
    r"i don'?t have enough information",
    r"i do not have enough information",
    r"i cannot answer",
    r"i can'?t answer",
    r"no information available to answer",
]

# Strong semantic match — always cite when answer is grounded.
MIN_CITATION_RERANK_SCORE = 2.0
# Weaker matches are allowed only for the top chunk with answer grounding.
MIN_WEAK_CITATION_SCORE = -8.0
MIN_ANSWER_TERM_OVERLAP = 3

_PRODUCT_QUERY = re.compile(
    r"\b(sensor|sensors|product|specification|necklace|wearable|iot|device|portfolio)\b",
    re.I,
)
_POLICY_QUERY = re.compile(
    r"\b(paid\s+time\s+off|vacation|handbook|policy|benefits|employee|remote\s+work)\b",
    re.I,
)
_LOCATION_QUERY = re.compile(
    r"\b(locations?|presence|offices?|where|headquarters|countries)\b",
    re.I,
)

_PRODUCT_DOC_HINTS = (
    "equine_and_sensors",
    "product_spec",
    "dairy_and_livestock",
    "solutions_and_markets",
    "company_overview",
    "agriculture_analytics",
)
_POLICY_DOC_HINTS = ("employee_handbook",)
_LOCATION_DOC_HINTS = ("company_overview", "solutions_and_markets")
_LOW_SIGNAL_DOC_HINTS = ("case_studies",)

_STOPWORDS = frozenset({
    "about", "after", "also", "and", "are", "been", "being", "both", "but",
    "can", "company", "could", "does", "from", "give", "had", "has", "have",
    "help", "here", "into", "kind", "like", "more", "most", "much", "only",
    "other", "over", "some", "such", "than", "that", "the", "their", "them",
    "then", "there", "these", "they", "this", "those", "through", "very",
    "what", "when", "where", "which", "while", "will", "with", "would", "your",
    "each", "with", "standard", "spans", "several", "global",
})


def is_insufficient_answer(response: str) -> bool:
    lower = (response or "").lower().strip()
    if len(lower) < 10:
        return True
    return any(re.search(pattern, lower) for pattern in REFUSAL_PATTERNS)


def _significant_terms(text: str) -> set[str]:
    return {
        word
        for word in re.findall(r"\b[a-z][a-z0-9]{3,}\b", (text or "").lower())
        if word not in _STOPWORDS
    }


def _grounding_phrases(response: str) -> list[str]:
    phrases = []
    lower = (response or "").lower()
    for match in re.finditer(r"\b\d+\s*(?:days?|years?|weeks?)\b", lower):
        phrases.append(match.group().strip())
    for match in re.finditer(
        r"\b(?:fremont|hyderabad|france|india|telangana|california|europe|tracy|palo\s+alto)\b",
        lower,
    ):
        phrases.append(match.group().strip())
    for match in re.finditer(r"\b(?:pto|vacation|remote\s+work)\b", lower):
        phrases.append(match.group().strip())
    return phrases


def _chunk_supports_answer(chunk_text: str, response: str) -> bool:
    chunk_lower = (chunk_text or "").lower()
    response_lower = (response or "").lower()

    overlap = _significant_terms(chunk_text) & _significant_terms(response)
    if len(overlap) >= MIN_ANSWER_TERM_OVERLAP:
        return True

    for phrase in _grounding_phrases(response):
        if phrase in chunk_lower:
            return True

    topical = {
        "sensor", "sensors", "necklace", "wearable", "dairy", "cattle",
        "iot", "equine", "veterinary", "rumination", "vacation", "handbook",
        "fremont", "hyderabad", "france", "telangana", "remote",
        "hanumayamma", "hanuinnotech", "innovations", "agriculture",
        "analytics", "livestock", "climate", "sustainability",
    }
    if len(overlap & topical) >= 2:
        return True

    return False


def _doc_title(title: str) -> str:
    return (title or "").lower()


def _prefer_topic_documents(chunks: list, query: str) -> list:
    if not chunks:
        return chunks

    if _PRODUCT_QUERY.search(query):
        preferred = [
            c for c in chunks
            if any(h in _doc_title(c.get("metadata", {}).get("title")) for h in _PRODUCT_DOC_HINTS)
        ]
        if preferred:
            return preferred

    if _POLICY_QUERY.search(query):
        preferred = [
            c for c in chunks
            if any(h in _doc_title(c.get("metadata", {}).get("title")) for h in _POLICY_DOC_HINTS)
        ]
        if preferred:
            return preferred

    if _LOCATION_QUERY.search(query):
        preferred = [
            c for c in chunks
            if any(h in _doc_title(c.get("metadata", {}).get("title")) for h in _LOCATION_DOC_HINTS)
        ]
        if preferred:
            return preferred

    return chunks


def _drop_low_signal_docs(chunks: list, query: str) -> list:
    if not chunks:
        return chunks
    if not (_PRODUCT_QUERY.search(query) or _POLICY_QUERY.search(query) or _LOCATION_QUERY.search(query)):
        return chunks

    focused = [
        c for c in chunks
        if not any(h in _doc_title(c.get("metadata", {}).get("title")) for h in _LOW_SIGNAL_DOC_HINTS)
    ]
    return focused or chunks


def _dedupe_documents(chunks: list, max_total: int = 3) -> list:
    seen_titles = set()
    unique = []
    for chunk in chunks:
        title = _doc_title(chunk.get("metadata", {}).get("title"))
        if title in seen_titles:
            continue
        seen_titles.add(title)
        unique.append(chunk)
        if len(unique) >= max_total:
            break
    return unique


def filter_relevant_chunks(
    top_chunks: list,
    query: str = "",
    response: str = "",
) -> list:
    if not top_chunks:
        return []

    ranked = sorted(
        top_chunks[:8],
        key=lambda chunk: chunk.get("rerank_score", -999),
        reverse=True,
    )[:5]

    if _LOCATION_QUERY.search(query):
        without_case_studies = [
            chunk for chunk in ranked
            if "case_studies" not in _doc_title(chunk.get("metadata", {}).get("title"))
        ]
        if without_case_studies:
            ranked = without_case_studies

    top_score = ranked[0].get("rerank_score", -999)

    selected = []
    for chunk in ranked:
        score = chunk.get("rerank_score", -999)
        if response and not _chunk_supports_answer(chunk.get("text", ""), response):
            continue

        if score >= MIN_CITATION_RERANK_SCORE:
            selected.append(chunk)
        elif (
            score >= MIN_WEAK_CITATION_SCORE
            and score >= top_score - 0.25
            and _chunk_supports_answer(chunk.get("text", ""), response)
        ):
            selected.append(chunk)

    selected = _prefer_topic_documents(selected, query)
    selected = _drop_low_signal_docs(selected, query)
    return _dedupe_documents(selected)


def _select_citation_chunks(
    top_chunks: list,
    query: str = "",
    response: str = "",
    context_chunks: list | None = None,
) -> list:
    selected = filter_relevant_chunks(top_chunks, query, response)
    if selected:
        return selected

    if (
        context_chunks
        and not is_insufficient_answer(response)
        and (response or "").strip()
    ):
        preferred = _prefer_topic_documents(context_chunks, query)
        preferred = _drop_low_signal_docs(preferred, query)
        return _dedupe_documents(preferred, max_total=3)

    return []


def should_attach_citations(
    response: str,
    top_chunks: list,
    intent: str = "factual",
    query: str = "",
    context_chunks: list | None = None,
) -> bool:
    if intent == "conversational":
        return False
    if not (response or "").strip():
        return False
    if is_insufficient_answer(response):
        return False
    pool = top_chunks or context_chunks
    if not pool:
        return False
    return bool(_select_citation_chunks(top_chunks, query, response, context_chunks))


def build_citation_payload(
    top_chunks: list,
    query: str = "",
    response: str = "",
    context_chunks: list | None = None,
) -> list:
    citations = []
    for chunk in _select_citation_chunks(top_chunks, query, response, context_chunks):
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
