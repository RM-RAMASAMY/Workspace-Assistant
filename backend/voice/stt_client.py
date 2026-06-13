import logging
import httpx
from config import settings
from .stt_corrections import normalize_transcript

_LISTEN_URL = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&punctuate=true"
_http: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(timeout=30.0)
    return _http


async def transcribe_audio(audio_data: bytes) -> str:
    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm",
    }

    if not settings.DEEPGRAM_API_KEY:
        return "Simulated STT: What is the current sensor specification?"

    if not audio_data or len(audio_data) < 1024:
        logging.warning(
            f"STT: audio too small to transcribe ({len(audio_data) if audio_data else 0} bytes)"
        )
        return ""

    response = await _get_client().post(
        _LISTEN_URL, headers=headers, content=audio_data
    )
    if response.status_code != 200:
        logging.error(f"Deepgram STT {response.status_code}: {response.text}")
        raise RuntimeError(
            f"Speech-to-text failed ({response.status_code}): {response.text[:300]}"
        )
    data = response.json()
    transcript = data["results"]["channels"][0]["alternatives"][0]["transcript"]
    return normalize_transcript(transcript)
