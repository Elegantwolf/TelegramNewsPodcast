"""Saved Messages reaction-tag resolution and message association."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class SavedMessageTag:
    """A stable, serializable Saved Messages tag association."""

    tag_id: str
    reaction_type: str
    reaction: str | int | None
    title: str | None
    display_name: str | None
    count: int | None
    chosen_order: int | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "tag_id": self.tag_id,
            "reaction_type": self.reaction_type,
            "reaction": self.reaction,
            "title": self.title,
            "display_name": self.display_name,
            "count": self.count,
            "chosen_order": self.chosen_order,
        }


@dataclass(frozen=True)
class SavedTagCatalog:
    """Cached account-level Saved Messages tag names and server hash."""

    tags: tuple[SavedMessageTag, ...] = ()
    hash: int | None = None
    supported: bool = False

    @property
    def by_id(self) -> dict[str, SavedMessageTag]:
        return {tag.tag_id: tag for tag in self.tags}


async def fetch_saved_tag_catalog(
    client: Any,
    *,
    peer: Any = None,
    previous_hash: int = 0,
    previous: SavedTagCatalog | None = None,
) -> SavedTagCatalog:
    """Fetch the user-defined Saved Messages tag catalog when supported.

    The request is optional enrichment.  Missing Telethon request types,
    unsupported account/API layers, unavailable tag metadata, and transient
    request failures return an empty or previous catalog rather than aborting
    the archive run.  ``previous_hash`` and ``previous`` allow callers to use
    Telegram's not-modified response as a local cache hit.
    """

    try:
        from telethon.tl.functions.messages import GetSavedReactionTagsRequest
    except (ImportError, AttributeError):
        return previous or SavedTagCatalog()

    try:
        result = await client(
            GetSavedReactionTagsRequest(peer=peer, hash=previous_hash)
        )
    except Exception:
        return previous or SavedTagCatalog()

    raw_tags = getattr(result, "tags", None)
    result_hash = _as_int(getattr(result, "hash", None))
    if raw_tags is None:
        if previous is not None:
            return SavedTagCatalog(
                tags=previous.tags,
                hash=result_hash if result_hash is not None else previous.hash,
                supported=previous.supported,
            )
        return SavedTagCatalog(hash=result_hash or previous_hash or None, supported=True)

    tags = tuple(
        parsed
        for raw_tag in raw_tags
        if (parsed := _parse_catalog_tag(raw_tag)) is not None
    )
    return SavedTagCatalog(tags=tags, hash=result_hash, supported=True)


def extract_saved_tags(
    message: Any,
    catalog: SavedTagCatalog | Mapping[str, SavedMessageTag] | None = None,
) -> tuple[SavedMessageTag, ...]:
    """Extract tags from one Telethon message's reaction metadata.

    Telegram distinguishes ordinary reactions from Saved Messages tags with
    the ``reactions_as_tags`` flag.  A false flag is therefore treated as no
    archive tags, while absent flag data remains best-effort compatible with
    older Telethon objects.
    """

    reactions = getattr(message, "reactions", None)
    if reactions is None or getattr(reactions, "reactions_as_tags", True) is False:
        return ()

    if isinstance(catalog, SavedTagCatalog):
        catalog_by_id = catalog.by_id
    else:
        catalog_by_id = dict(catalog or {})

    parsed_tags: list[SavedMessageTag] = []
    seen_ids: set[str] = set()
    for reaction_count in getattr(reactions, "results", None) or ():
        parsed = _parse_message_tag(reaction_count, catalog_by_id)
        if parsed is None or parsed.tag_id in seen_ids:
            continue
        seen_ids.add(parsed.tag_id)
        parsed_tags.append(parsed)

    return tuple(parsed_tags)


def _parse_catalog_tag(raw_tag: Any) -> SavedMessageTag | None:
    reaction = getattr(raw_tag, "reaction", None)
    identity = _reaction_identity(reaction)
    if identity is None:
        return None

    tag_id, reaction_type, reaction_value = identity
    title = _clean_title(getattr(raw_tag, "title", None))
    return SavedMessageTag(
        tag_id=tag_id,
        reaction_type=reaction_type,
        reaction=reaction_value,
        title=title,
        display_name=title or _reaction_display_name(reaction_type, reaction_value),
        count=_as_int(getattr(raw_tag, "count", None)),
        chosen_order=None,
    )


def _parse_message_tag(
    reaction_count: Any,
    catalog_by_id: Mapping[str, SavedMessageTag],
) -> SavedMessageTag | None:
    reaction = getattr(reaction_count, "reaction", None)
    identity = _reaction_identity(reaction)
    if identity is None:
        return None

    tag_id, reaction_type, reaction_value = identity
    catalog_tag = catalog_by_id.get(tag_id)
    title = catalog_tag.title if catalog_tag else None
    return SavedMessageTag(
        tag_id=tag_id,
        reaction_type=reaction_type,
        reaction=reaction_value,
        title=title,
        display_name=title or _reaction_display_name(reaction_type, reaction_value),
        count=_as_int(getattr(reaction_count, "count", None)),
        chosen_order=_as_int(getattr(reaction_count, "chosen_order", None)),
    )


def _reaction_identity(
    reaction: Any,
) -> tuple[str, str, str | int | None] | None:
    if reaction is None:
        return None

    emoticon = getattr(reaction, "emoticon", None)
    if emoticon is not None:
        value = str(emoticon)
        # Telegram treats emoji variation selectors as presentation details;
        # omit them from the stable key while retaining the original value.
        stable_value = value.replace("\ufe0f", "")
        return f"emoji:{stable_value}", "emoji", value

    document_id = _as_int(getattr(reaction, "document_id", None))
    if document_id is not None:
        return f"custom_emoji:{document_id}", "custom_emoji", document_id

    reaction_type = type(reaction).__name__
    return f"reaction:{reaction_type}", reaction_type, None


def _reaction_display_name(
    reaction_type: str,
    reaction: str | int | None,
) -> str | None:
    if reaction_type == "emoji" and isinstance(reaction, str):
        return reaction
    return None


def _clean_title(value: Any) -> str | None:
    if value is None:
        return None
    title = str(value).strip()
    return title or None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


__all__ = [
    "SavedMessageTag",
    "SavedTagCatalog",
    "extract_saved_tags",
    "fetch_saved_tag_catalog",
]
