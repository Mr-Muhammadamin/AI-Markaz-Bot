"""
AI provayderlar registri.
Har bir provayder BaseProvider dan meros oladi va `ask(messages)` metodiga ega.
"""
from app.config import settings
from app.providers.base import BaseProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.claude_provider import ClaudeProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.deepseek_provider import DeepSeekProvider
from app.providers.openrouter_provider import OpenRouterProvider
from app.providers.groq_provider import GroqProvider

_PROVIDER_CLASSES = {
    "openai": OpenAIProvider,
    "claude": ClaudeProvider,
    "gemini": GeminiProvider,
    "deepseek": DeepSeekProvider,
    "openrouter": OpenRouterProvider,
    "groq": GroqProvider,
}

_instances: dict[str, BaseProvider] = {}


def get_provider(key: str) -> BaseProvider | None:
    """Berilgan kalit uchun provayder instansiyasini qaytaradi (agar yoqilgan bo'lsa)."""
    cfg = settings.providers.get(key)
    if not cfg or not cfg.enabled:
        return None

    if key not in _instances:
        cls = _PROVIDER_CLASSES[key]
        _instances[key] = cls(key, cfg)
    return _instances[key]


def list_all() -> list[str]:
    """Barcha mavjud provayder kalitlarini (yoqilgan/o'chirilganidan qat'i nazar) qaytaradi."""
    return list(settings.providers.keys())


def list_enabled() -> list[str]:
    """Faqat API kaliti kiritilgan (yoqilgan) provayderlar kalitlarini qaytaradi."""
    return [k for k, cfg in settings.providers.items() if cfg.enabled]
