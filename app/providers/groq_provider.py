"""Groq provayderi - OpenAI API formatiga mos keladi (bepul)."""
from openai import AsyncOpenAI

from app.providers.base import BaseProvider


class GroqProvider(BaseProvider):
    def __init__(self, key, config):
        super().__init__(key, config)
        self._client = AsyncOpenAI(
            api_key=config.api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    async def ask(self, messages: list[dict]) -> str:
        try:
            resp = await self._client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                temperature=0.7,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            raise RuntimeError(f"Groq xatolik: {e}") from e