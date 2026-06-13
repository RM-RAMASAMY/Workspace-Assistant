import re

_SENTENCE_END = re.compile(r"(?<=[.!?])\s+")
_CLAUSE_END = re.compile(r"(?<=,)\s+")


async def sentence_streamer(llm_token_generator, *, early_chars: int = 48):
    """
    Yield complete sentences for TTS. Flushes an early clause so the user
  sees (and hears) the first part sooner on long replies.
    """
    buffer = ""
    early_sent = False

    async for token in llm_token_generator:
        buffer += token

        if not early_sent and len(buffer) >= early_chars:
            clause_parts = _CLAUSE_END.split(buffer, maxsplit=1)
            if len(clause_parts) > 1 and len(clause_parts[0].strip()) >= 24:
                yield clause_parts[0].strip()
                buffer = clause_parts[1]
                early_sent = True
                continue

        splits = _SENTENCE_END.split(buffer)
        if len(splits) > 1:
            for sentence in splits[:-1]:
                stripped = sentence.strip()
                if stripped:
                    yield stripped
                    early_sent = True
            buffer = splits[-1]

    if buffer.strip():
        yield buffer.strip()
