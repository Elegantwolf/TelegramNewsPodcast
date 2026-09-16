"""Retrieve Saved Messages into dependency-light raw records."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Mapping

from .hashtags import extract_hashtags
from .tags import SavedMessageTag, SavedTagCatalog, extract_saved_tags


@dataclass(frozen=True)
class RawSavedMessage:
    """Raw Saved Message data needed by later archive normalization tasks.

    The record contains plain Python values only.  In particular, it does not
    retain a Telethon message object, so it can safely cross the fetch/archive
    boundary and be tested without a Telegram connection.
    """

    telegram_id: int
    saved_at: datetime | None
    edited_at: datetime | None
    grouped_id: int | None
    reply: Mapping[str, Any] | None
    text: str
    forward: Mapping[str, Any] | None
    saved_tags: tuple[SavedMessageTag, ...] = ()
    hashtags: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        """Return a JSON-ready representation for downstream normalization."""

        data = asdict(self)
        data["saved_at"] = _datetime_to_iso(self.saved_at)
        data["edited_at"] = _datetime_to_iso(self.edited_at)
        data["saved_tags"] = [tag.as_dict() for tag in self.saved_tags]
        data["hashtags"] = list(self.hashtags)
        return data


async def fetch_saved_messages(
    client: Any,
    *,
    limit: int | None = None,
    tag_catalog: SavedTagCatalog | None = None,
) -> list[RawSavedMessage]:
    """Fetch Saved Messages and return them in chronological order.

    ``limit=None`` performs the full initial scan.  A non-negative ``limit``
    is useful for bounded offline or account validation runs.  Telethon's
    native ordering is not relied on: records are always sorted by saved time
    and then Telegram message ID for deterministic results.
    """

    if limit is not None and limit < 0:
        raise ValueError("limit must be non-negative or None")
    if limit == 0:
        return []

    records: list[RawSavedMessage] = []
    async for message in client.iter_messages("me", limit=limit):
        records.append(_raw_record_from_message(message, tag_catalog=tag_catalog))

    records.sort(key=lambda record: (_datetime_sort_key(record.saved_at), record.telegram_id))
    return records


async def iter_saved_messages(
    client: Any,
    *,
    limit: int | None = None,
    tag_catalog: SavedTagCatalog | None = None,
) -> AsyncIterator[RawSavedMessage]:
    """Yield the deterministically ordered Saved Message records."""

    for record in await fetch_saved_messages(
        client,
        limit=limit,
        tag_catalog=tag_catalog,
    ):
        yield record


def _raw_record_from_message(
    message: Any,
    *,
    tag_catalog: SavedTagCatalog | None = None,
) -> RawSavedMessage:
    message_id = _as_int(getattr(message, "id", None))
    if message_id is None:
        raise ValueError("Saved Message has no Telegram message ID")

    text = getattr(message, "text", None) or ""
    return RawSavedMessage(
        telegram_id=message_id,
        saved_at=_as_datetime(getattr(message, "date", None)),
        edited_at=_as_datetime(getattr(message, "edit_date", None)),
        grouped_id=_as_int(getattr(message, "grouped_id", None)),
        reply=_reply_metadata(message),
        # ``text`` includes captions and may be None for media-only messages.
        text=text,
        forward=_forward_metadata(getattr(message, "fwd_from", None)),
        saved_tags=extract_saved_tags(message, tag_catalog),
        hashtags=extract_hashtags(text),
    )


def _reply_metadata(message: Any) -> dict[str, Any] | None:
    reply = getattr(message, "reply_to", None)
    if reply is None and getattr(message, "reply_to_msg_id", None) is None:
        return None

    return {
        "type": type(reply).__name__ if reply is not None else None,
        "reply_to_msg_id": _as_int(
            getattr(reply, "reply_to_msg_id", None)
            if reply is not None
            else getattr(message, "reply_to_msg_id", None)
        ),
        "reply_to_top_id": _as_int(getattr(reply, "reply_to_top_id", None)),
        "reply_to_peer": _peer_reference(getattr(reply, "reply_to_peer_id", None)),
    }


def _forward_metadata(header: Any) -> dict[str, Any] | None:
    if header is None:
        return None

    return {
        "type": type(header).__name__,
        "from_peer": _peer_reference(getattr(header, "from_id", None)),
        "from_name": getattr(header, "from_name", None),
        "channel_post": _as_int(getattr(header, "channel_post", None)),
        "date": _datetime_to_iso(_as_datetime(getattr(header, "date", None))),
        "post_author": getattr(header, "post_author", None),
        "saved_from_peer": _peer_reference(getattr(header, "saved_from_peer", None)),
        "saved_from_msg_id": _as_int(getattr(header, "saved_from_msg_id", None)),
    }


def _peer_reference(peer: Any) -> dict[str, Any] | None:
    if peer is None:
        return None

    for attribute, peer_type in (
        ("channel_id", "channel"),
        ("chat_id", "group"),
        ("user_id", "user"),
    ):
        peer_id = _as_int(getattr(peer, attribute, None))
        if peer_id is not None:
            return {"type": peer_type, "id": peer_id}

    # Preserve the concrete Telethon peer type even when it has no exposed ID.
    return {"type": type(peer).__name__, "id": None}


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _as_datetime(value: Any) -> datetime | None:
    return value if isinstance(value, datetime) else None


def _datetime_to_iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


def _datetime_sort_key(value: datetime | None) -> datetime:
    if value is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


__all__ = ["RawSavedMessage", "fetch_saved_messages", "iter_saved_messages"]
