"""WhatsApp settings. Everything comes from environment variables."""

import os
from dataclasses import dataclass, field
from typing import List


def _numbers(raw: str) -> List[str]:
    return [n.strip().lstrip("+").replace(" ", "") for n in raw.split(",") if n.strip()]


@dataclass
class WhatsAppConfig:
    access_token: str = field(default_factory=lambda: os.getenv("WA_ACCESS_TOKEN", ""))
    phone_number_id: str = field(default_factory=lambda: os.getenv("WA_PHONE_NUMBER_ID", ""))
    app_secret: str = field(default_factory=lambda: os.getenv("WA_APP_SECRET", ""))
    verify_token: str = field(default_factory=lambda: os.getenv("WA_VERIFY_TOKEN", ""))
    api_version: str = field(default_factory=lambda: os.getenv("WA_API_VERSION", "v21.0"))
    # Which AI employee answers: "saira_procurement" or "designrite_aanya"
    persona: str = field(default_factory=lambda: os.getenv("WA_PERSONA", "saira_procurement"))
    # Owner numbers (international format, no +). Owner can send STOP BOT / START BOT.
    owner_numbers: List[str] = field(default_factory=lambda: _numbers(os.getenv("WA_OWNER_NUMBERS", "")))
    # If set, the bot only answers these numbers (e.g. Saira staff). Empty = answer anyone.
    allowed_numbers: List[str] = field(default_factory=lambda: _numbers(os.getenv("WA_ALLOWED_NUMBERS", "")))
    # Master switch. "off" = log messages but never auto-reply.
    autoreply: bool = field(default_factory=lambda: os.getenv("WA_AUTOREPLY", "on").lower() != "off")
    # Loop guard: max bot replies to one contact inside the window.
    max_replies_per_window: int = field(default_factory=lambda: int(os.getenv("WA_MAX_REPLIES", "5")))
    window_minutes: int = field(default_factory=lambda: int(os.getenv("WA_WINDOW_MINUTES", "10")))

    @property
    def can_send(self) -> bool:
        return bool(self.access_token and self.phone_number_id)

    @property
    def graph_base(self) -> str:
        return f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}"
