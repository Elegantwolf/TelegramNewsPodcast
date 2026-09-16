"""Shared Telegram client and session configuration.

Telethon is imported only when a client is created.  This keeps configuration
and offline archive utilities importable on machines that do not have the
Telegram dependency installed.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo


DEFAULT_TIMEZONE = "Asia/Tokyo"


@dataclass(frozen=True)
class TelegramClientConfig:
    """Settings shared by channel fetching and Saved Messages ingestion.

    ``session_path`` may be a Telethon session name or a filesystem path.  It
    must point to local client configuration storage, never to the NAS archive
    root.  A recommended explicit path is
    ``~/.config/telegram-news-podcast/telegram.session``.
    """

    api_id: int
    api_hash: str
    session_path: str | Path
    timezone: str = DEFAULT_TIMEZONE

    def __post_init__(self) -> None:
        if not isinstance(self.api_id, int) or self.api_id <= 0:
            raise ValueError("api_id must be a positive integer")
        if not self.api_hash or not self.api_hash.strip():
            raise ValueError("api_hash must not be empty")
        if not str(self.session_path).strip():
            raise ValueError("session_path must not be empty")
        if not self.timezone or not self.timezone.strip():
            raise ValueError("timezone must not be empty")

    @property
    def local_timezone(self) -> ZoneInfo:
        """Return the configured timezone for timestamp normalization."""

        return ZoneInfo(self.timezone)


def create_telegram_client(
    config: TelegramClientConfig,
    **client_kwargs: Any,
) -> Any:
    """Create an asynchronous Telethon client from shared settings.

    The import is deliberately local so importing this project does not
    require Telethon unless a Telegram operation is actually started.  Parent
    directories are created for explicit filesystem session paths; a simple
    session name such as ``my_telegram_session`` continues to work relative to
    the current directory for backward compatibility.
    """

    from telethon import TelegramClient

    session_path = Path(config.session_path).expanduser()
    session_path.parent.mkdir(parents=True, exist_ok=True)
    return TelegramClient(
        str(session_path),
        config.api_id,
        config.api_hash,
        **client_kwargs,
    )


__all__ = ["DEFAULT_TIMEZONE", "TelegramClientConfig", "create_telegram_client"]
