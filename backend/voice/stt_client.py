import httpx
from config import settings

async def transcribe_audio(audio_data: bytes) -> str:
    url = "https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true"
    headers = {
        "Authorization": f"Token {settings.DEEPGRAM_API_KEY}",
        "Content-Type": "audio/webm"
    }
    
    if not settings.DEEPGRAM_API_KEY:
        # Fallback for dev without keys
        return "Simulated STT: What is the current sensor specification?"

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, content=audio_data)
        response.raise_for_status()
        data = response.json()
        return data["results"]["channels"][0]["alternatives"][0]["transcript"]
