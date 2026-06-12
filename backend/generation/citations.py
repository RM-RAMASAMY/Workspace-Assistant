import re

# UUID citations (【id】 or [id]) and numeric footnotes like [1].
CITATION_MARKER_RE = re.compile(
    r"[\[【]\s*[a-f0-9-]{36}\s*[\]】]|\[\d+\]",
    re.IGNORECASE,
)


def strip_citation_markers(text: str) -> str:
    cleaned = CITATION_MARKER_RE.sub("", text or "")
    return re.sub(r"\s{2,}", " ", cleaned).strip()
