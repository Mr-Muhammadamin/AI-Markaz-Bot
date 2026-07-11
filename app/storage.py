from dataclasses import dataclass, field

MAX_HISTORY_MESSAGES = 20


@dataclass
class UserSession:
    provider_key: str | None = None
    history: list[dict] = field(default_factory=list)

    def add_user_message(self, content: str):
        self.history.append({"role": "user", "content": content})
        self._trim()

    def add_assistant_message(self, content: str):
        self.history.append({"role": "assistant", "content": content})
        self._trim()

    def reset(self):
        self.history.clear()

    def _trim(self):
        if len(self.history) > MAX_HISTORY_MESSAGES:
            self.history = self.history[-MAX_HISTORY_MESSAGES:]


_sessions: dict[int, UserSession] = {}


def get_session(user_id: int) -> UserSession:
    if user_id not in _sessions:
        _sessions[user_id] = UserSession()
    return _sessions[user_id]