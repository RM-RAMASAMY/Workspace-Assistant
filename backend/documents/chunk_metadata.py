import re
from .chunker import recursive_character_chunker


def _section_at(text: str, position: int) -> str:
    """Return the nearest markdown heading at or before position."""
    section = ""
    for match in re.finditer(r"^#{1,3}\s+(.+)$", text, re.MULTILINE):
        if match.start() <= position:
            section = match.group(1).strip()
        else:
            break
    return section


def build_chunks_with_metadata(text: str, chunk_size: int = 1000, chunk_overlap: int = 100):
    """Chunk text and attach section title plus line range for each chunk."""
    raw_chunks = recursive_character_chunker(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    enriched = []
    search_from = 0

    for index, chunk_text in enumerate(raw_chunks):
        position = text.find(chunk_text, search_from)
        if position < 0:
            position = text.find(chunk_text)

        if position >= 0:
            line_start = text[:position].count("\n") + 1
            line_end = line_start + chunk_text.count("\n")
            search_from = position + max(len(chunk_text) - chunk_overlap, 1)
        else:
            line_start = 0
            line_end = 0

        enriched.append(
            {
                "text": chunk_text,
                "chunk_index": index,
                "section_title": _section_at(text, position if position >= 0 else 0),
                "line_start": line_start,
                "line_end": line_end,
            }
        )

    return enriched
