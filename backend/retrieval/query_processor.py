import re

# Expand common STT variants and aliases so retrieval matches company docs.
_COMPANY_QUERY_ALIASES = [
    (re.compile(r"\bhanoi\s+note\s+tech\b", re.I), "Hannu InnoTech Hanumayamma Innovations and Technologies"),
    (re.compile(r"\bhanu\s+innotech\b", re.I), "Hannu InnoTech Hanumayamma Innovations and Technologies"),
    (re.compile(r"\bhannu\s+innotech\b", re.I), "Hannu InnoTech Hanumayamma Innovations and Technologies"),
    (re.compile(r"\bhanumayamma\b", re.I), "Hanumayamma Innovations and Technologies Hannu InnoTech"),
]

_TOPIC_EXPANSIONS = [
    (
        re.compile(r"\bsensors?\b", re.I),
        "Hannu InnoTech sensor portfolio dairy cow necklace wearable veterinary IoT equine Hayagriva Class 10",
    ),
    (
        re.compile(r"\bpaid\s+time\s+off\b|\bvacation\s+policy\b", re.I),
        "employee handbook paid time off vacation remote work days",
    ),
    (
        re.compile(r"\blocations?\b|\bpresence\b|\boffices?\b", re.I),
        "company global offices Fremont Hyderabad France United States India Europe",
    ),
    (
        re.compile(r"\bdairy\b|\bcow\b|\bcattle\b|\brumination\b", re.I),
        "dairy livestock cow necklace rumination Hanumayamma dairy analytics",
    ),
    (
        re.compile(r"\bspec(ification)?s?\b", re.I),
        "product specification technical datasheet sensor accuracy calibration",
    ),
]

_CONVERSATIONAL_PATTERNS = [
    r"^(hi|hello|hey|yo|good morning|good afternoon|good evening)\b",
    r"\bhow are you\b",
    r"\bhow'?s it going\b",
    r"\bwhat'?s up\b",
    r"\bwassup\b",
    r"^(thanks|thank you|thx)\b",
    r"\bwho are you\b",
    r"^(bye|goodbye|see you|later)\b",
    r"\bnice to meet you\b",
    r"\bgood (?:morning|afternoon|evening|night)\b",
]

# Factual cue words — only checked after conversational patterns fail.
_FACTUAL_HINTS = re.compile(
    r"\b(who|when|where|why|how many|how much|tell me|explain|describe|"
    r"summary|summarize|list|calibrat|pto|company|product|sensor|dairy|"
    r"agriculture|cow|necklace|hanu|hanumayamma|document|policy|employee|"
    r"specification|mission|vision|location|office)\b",
    re.I,
)


def _expand_company_aliases(query: str) -> str:
    expanded = query
    for pattern, replacement in _COMPANY_QUERY_ALIASES:
        if pattern.search(expanded):
            expanded = f"{expanded} {replacement}"
    return expanded.strip()


def _disambiguate_pto(query: str) -> str:
    """Avoid confusing paid time off with USPTO trademark mentions in ag/dairy docs."""
    if re.search(r"\bptos?\b", query, re.I) and not re.search(r"\buspto\b", query, re.I):
        return re.sub(
            r"\bptos?\b",
            "paid time off vacation leave employee handbook",
            query,
            flags=re.I,
        )
    return query


def _expand_topic_aliases(query: str) -> str:
    expanded = _disambiguate_pto(query)
    for pattern, extra in _TOPIC_EXPANSIONS:
        if pattern.search(expanded):
            expanded = f"{expanded} {extra}"
    return expanded.strip()


def is_conversational(transcription: str) -> bool:
    text = (transcription or "").strip()
    if not text:
        return False
    lower = re.sub(r"[^\w\s']", " ", text.lower())
    lower = re.sub(r"\s+", " ", lower).strip()
    if len(lower) > 80:
        return False
    # Greetings/small-talk win before broad factual keywords (e.g. "what" in "what's up").
    if any(re.search(pattern, lower) for pattern in _CONVERSATIONAL_PATTERNS):
        return True
    if _FACTUAL_HINTS.search(lower):
        return False
    return False


MAX_HISTORY_MESSAGES = 12
MAX_HISTORY_CHARS = 1000


def _normalize_history(history: list) -> list:
    turns = []
    for item in history or []:
        role = item.get("role")
        content = (item.get("content") or "").strip()
        if role not in ("user", "assistant") or not content:
            continue
        turns.append({
            "role": role,
            "content": content[:MAX_HISTORY_CHARS],
        })
    return turns[-MAX_HISTORY_MESSAGES:]


def _build_search_query(transcription: str, history: list) -> str:
    """Expand retrieval query with recent turns for follow-up questions."""
    if not history:
        return transcription

    recent = _normalize_history(history)
    user_turns = [t["content"] for t in recent if t["role"] == "user"][-2:]
    assistant_turns = [t["content"] for t in recent if t["role"] == "assistant"][-1:]

    parts = [transcription]
    if user_turns:
        parts.append(" ".join(user_turns))
    if assistant_turns:
        parts.append(assistant_turns[-1][:300])
    return " ".join(parts)


def process_query(transcription: str, history: list | None = None):
    history = _normalize_history(history)
    rewritten = _expand_company_aliases(transcription)
    rewritten = _expand_topic_aliases(rewritten)
    search_query = _build_search_query(rewritten, history)
    intent = "conversational" if is_conversational(transcription) else "factual"

    return {
        "rewritten": rewritten,
        "search_query": search_query,
        "history": history,
        "variants": [search_query],
        "intent": intent,
    }
