import httpx
import json
from config import settings

_VOICE_OPTIONS = {
    # Budget for internal reasoning + spoken answer when think=True.
    "num_predict": 1024,
    "temperature": 0.4,
}

MAX_LLM_HISTORY = 12


class OllamaClient:
    def __init__(self):
        self.base_url = settings.OLLAMA_BASE_URL
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            timeout = httpx.Timeout(connect=10.0, read=120.0, write=30.0, pool=10.0)
            self._client = httpx.AsyncClient(timeout=timeout)
        return self._client

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str,
        history: list | None = None,
        model=None,
    ):
        if model is None:
            model = settings.OLLAMA_MODEL
        url = f"{self.base_url}/api/chat"

        messages = [{"role": "system", "content": system_prompt}]
        for turn in (history or [])[-MAX_LLM_HISTORY:]:
            role = turn.get("role")
            content = (turn.get("content") or "").strip()
            if role in ("user", "assistant") and content:
                messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "think": True,
            "keep_alive": "10m",
            "options": _VOICE_OPTIONS,
        }

        client = self._get_client()
        try:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        message = data.get("message") or {}
                        # Stream only the user-facing answer; thinking stays hidden.
                        content = message.get("content") or ""
                        if content:
                            yield content
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            yield f"Error connecting to LLM: {str(e)}"
