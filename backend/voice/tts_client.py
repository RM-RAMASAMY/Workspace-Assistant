import logging
import httpx
from config import settings

async def synthesize_speech(text: str) -> bytes:
    voice_id = settings.ELEVENLABS_VOICE_ID
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
    headers = {
        "xi-api-key": settings.ELEVENLABS_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "text": text,
        "model_id": "eleven_flash_v2_5",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    if not settings.ELEVENLABS_API_KEY:
        # Fallback empty audio
        return b""

    # TTS is best-effort: if the key is invalid/rate-limited or the service is
    # unreachable, we must NOT break the chat. Return empty audio so the text
    # response still streams to the client.
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.content
    except Exception as e:
        logging.warning(f"TTS synthesis failed; continuing without audio: {e}")
        return b""
