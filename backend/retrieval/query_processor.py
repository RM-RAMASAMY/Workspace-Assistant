import re

# Expand common STT variants and aliases so retrieval matches company docs.
_COMPANY_QUERY_ALIASES = [
    (re.compile(r"\bhanoi\s+note\s+tech\b", re.I), "Hannu InnoTech Hanumayamma Innovations and Technologies"),
    (re.compile(r"\bhanu\s+innotech\b", re.I), "Hannu InnoTech Hanumayamma Innovations and Technologies"),
    (re.compile(r"\bhannu\s+innotech\b", re.I), "Hannu InnoTech Hanumayamma Innovations and Technologies"),
    (re.compile(r"\bhanumayamma\b", re.I), "Hanumayamma Innovations and Technologies Hannu InnoTech"),
]

_CONVERSATIONAL_PATTERNS = [
    r"^(hi|hello|hey|yo|good morning|good afternoon|good evening)\b",
    r"\bhow are you\b",
    r"\bhow'?s it going\b",
    r"\bwhat'?s up\b",
    r"^(thanks|thank you)\b",
    r"\bwho are you\b",
    r"^(bye|goodbye|see you)\b",
    r"\bnice to meet you\b",
]

_FACTUAL_HINTS = re.compile(
    r"\b(what|who|when|where|why|how many|how much|tell me|explain|describe|"
    r"pto|company|product|sensor|dairy|agriculture|cow|necklace|hanu|hanumayamma|"
    r"document|policy|employee|specification)\b",
    re.I,
)


def _expand_company_aliases(query: str) -> str:
    expanded = query
    for pattern, replacement in _COMPANY_QUERY_ALIASES:
        if pattern.search(expanded):
            expanded = f"{expanded} {replacement}"
    return expanded.strip()


def is_conversational(transcription: str) -> bool:
    text = (transcription or "").strip()
    if not text:
        return False
    lower = text.lower()
    if _FACTUAL_HINTS.search(lower):
        return False
    if len(lower) > 80:
        return False
    return any(re.search(pattern, lower) for pattern in _CONVERSATIONAL_PATTERNS)


def process_query(transcription: str, history: list):
    rewritten = _expand_company_aliases(transcription)
    intent = "conversational" if is_conversational(transcription) else "factual"

    return {
        "rewritten": rewritten,
        "variants": [rewritten],
        "intent": intent,
    }
