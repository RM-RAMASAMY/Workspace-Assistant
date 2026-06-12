import re

# Common mis-hearings of company / product names from voice input.
_PHRASE_CORRECTIONS = [
    (re.compile(r"\bhanoi\s+note\s+tech\b", re.I), "Hannu InnoTech"),
    (re.compile(r"\bhanu\s+inno\s+tech\b", re.I), "Hannu InnoTech"),
    (re.compile(r"\bhanu\s+innotech\b", re.I), "Hannu InnoTech"),
    (re.compile(r"\bhanumayama\b", re.I), "Hanumayamma"),
    (re.compile(r"\bhanu\s+mayamma\b", re.I), "Hanumayamma"),
    (re.compile(r"\bhanumayamma\s+innovations\b", re.I), "Hanumayamma Innovations and Technologies"),
]


def normalize_transcript(transcript: str) -> str:
    text = (transcript or "").strip()
    for pattern, replacement in _PHRASE_CORRECTIONS:
        text = pattern.sub(replacement, text)
    return text
