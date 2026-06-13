import logging
import httpx
from config import settings

_http: httpx.AsyncClient | None = None


def _get_client() -> httpx.AsyncClient:
    global _http
    if _http is None or _http.is_closed:
        _http = httpx.AsyncClient(timeout=30.0)
    return _http


async def synthesize_speech(text: str) -> bytes:
    voice_id = settings.ELEVENLABS_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5,
        },
    }

    if not settings.ELEVENLABS_API_KEY:
        return b""

    try:
        response = await _get_client().post(url, headers=headers, json=payload)
        response.raise_for_status()
        return response.content
    except Exception as e:
        logging.warning(f"TTS synthesis failed; continuing without audio: {e}")
        return b""
