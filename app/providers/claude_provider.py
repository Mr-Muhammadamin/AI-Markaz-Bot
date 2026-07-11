from anthropic import AsyncAnthropic
from app.providers.base import BaseProvider


class ClaudeProvider(BaseProvider):
    def __init__(self, key, config):
        super().__init__(key, config)
        self._client = AsyncAnthropic(api_key=config.api_key)

    async def ask(self, messages: list[dict]) -> str:
        try:
            system_prompt = ""
            chat_messages = []
            for m in messages:
                if m["role"] == "system":
                    system_prompt += m["content"] + "\n"
                else:
                    chat_messages.append(m)

            resp = await self._client.messages.create(
                model=self.config.model,
                max_tokens=4096,
                system=system_prompt or None,
                messages=chat_messages,
            )
            parts = [block.text for block in resp.content if getattr(block, "type", "") == "text"]
            return "\n".join(parts)
        except Exception as e:
            raise RuntimeError(f"Claude xatolik: {e}") from e