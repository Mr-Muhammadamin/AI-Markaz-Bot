import asyncio
import logging

import google.generativeai as genai

from app.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class GeminiProvider(BaseProvider):
    def __init__(self, key, config):
        super().__init__(key, config)
        genai.configure(api_key=config.api_key)
        self._model = genai.GenerativeModel(config.model)

    async def ask(self, messages: list[dict]) -> str:
        system_parts = [m["content"] for m in messages if m["role"] == "system"]
        history = []
        for m in messages:
            if m["role"] == "system":
                continue
            role = "model" if m["role"] == "assistant" else "user"
            history.append({"role": role, "parts": [m["content"]]})

        if system_parts and history:
            for h in history:
                if h["role"] == "user":
                    h["parts"][0] = "\n".join(system_parts) + "\n\n" + h["parts"][0]
                    break

        last_exception = None
        max_retries = 3

        for attempt in range(max_retries + 1):
            try:
                def _generate():
                    resp = self._model.generate_content(history)
                    return resp.text

                loop = asyncio.get_event_loop()
                text = await loop.run_in_executor(None, _generate)
                return text or ""
            except Exception as e:
                error_str = str(e)
                last_exception = e

                if "429" in error_str or "quota" in error_str.lower() or "Quota exceeded" in error_str:
                    if attempt < max_retries:
                        wait = 2 ** attempt * 5
                        logger.warning(f"Gemini 429 (quota) xatolik, {wait}s kutib qayta urinaman (urinsh {attempt+1}/{max_retries})")
                        await asyncio.sleep(wait)
                        continue

                raise RuntimeError(f"Gemini xatolik: {e}") from e

        raise RuntimeError(f"Gemini xatolik (quota): {last_exception}") from last_exception