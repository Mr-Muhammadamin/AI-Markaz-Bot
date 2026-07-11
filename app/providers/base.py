from abc import ABC, abstractmethod
from app.config import ProviderConfig


class BaseProvider(ABC):
    def __init__(self, key: str, config: ProviderConfig):
        self.key = key
        self.config = config

    @property
    def display_name(self) -> str:
        return self.config.name

    @abstractmethod
    async def ask(self, messages: list[dict]) -> str:
        """
        messages: [{"role": "user"|"assistant"|"system", "content": "..."}]
        Modelning javob matnini qaytaradi.
        Xatolik bo'lsa, tushunarli xabar bilan Exception ko'tarilishi kerak.
        """
        raise NotImplementedError