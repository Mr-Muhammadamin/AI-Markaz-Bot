import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _get_int_list(raw: str) -> list[int]:
    if not raw:
        return []
    result = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            result.append(int(part))
    return result


@dataclass
class ProviderConfig:
    name: str
    api_key: str
    model: str
    enabled: bool = field(init=False)

    def __post_init__(self):
        self.enabled = bool(self.api_key)


@dataclass
class Settings:
    telegram_bot_token: str
    allowed_user_ids: list[int]
    providers: dict[str, ProviderConfig]
    default_provider: str


def load_settings() -> Settings:
    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    allowed_user_ids = _get_int_list(os.getenv("ALLOWED_USER_IDS", ""))

    providers = {
        "openai": ProviderConfig(
            name="OpenAI (ChatGPT)",
            api_key=os.getenv("OPENAI_API_KEY", "").strip(),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        ),
        "claude": ProviderConfig(
            name="Anthropic Claude",
            api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
        ),
        "gemini": ProviderConfig(
            name="Google Gemini",
            api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            model=os.getenv("GEMINI_MODEL", "gemini-1.5-pro"),
        ),
        "deepseek": ProviderConfig(
            name="DeepSeek",
            api_key=os.getenv("DEEPSEEK_API_KEY", "").strip(),
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        ),
        "openrouter": ProviderConfig(
            name="OpenRouter",
            api_key=os.getenv("OPENROUTER_API_KEY", "").strip(),
            model=os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini"),
        ),
        "groq": ProviderConfig(
            name="Groq",
            api_key=os.getenv("GROQ_API_KEY", "").strip(),
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        ),
    }

    default_provider = ""
    for key, cfg in providers.items():
        if cfg.enabled:
            default_provider = key
            break

    return Settings(
        telegram_bot_token=telegram_bot_token,
        allowed_user_ids=allowed_user_ids,
        providers=providers,
        default_provider=default_provider,
    )


settings = load_settings()