"""Deterministic extraction of ordinary hashtags from message text."""

from __future__ import annotations

import unicodedata


def extract_hashtags(text: str | None) -> tuple[str, ...]:
    """Return normalized, first-seen hashtags without their ``#`` prefix.

    Unicode letters, numbers, combining marks, and underscores are accepted.
    Matching is deliberately conservative around ``foo#bar``, ``C#`` and
    repeated hash characters.  Duplicate values are compared with Unicode
    ``casefold`` while retaining the first occurrence's spelling.
    """

    if not text:
        return ()

    hashtags: list[str] = []
    seen: set[str] = set()
    text_length = len(text)
    index = 0

    while index < text_length:
        if text[index] != "#" or not _valid_hash_boundary(text, index):
            index += 1
            continue

        value_start = index + 1
        value_end = value_start
        while value_end < text_length and _is_hashtag_character(text[value_end]):
            value_end += 1

        if value_end == value_start:
            index += 1
            continue

        value = unicodedata.normalize("NFC", text[value_start:value_end])
        dedupe_key = value.casefold()
        if dedupe_key not in seen:
            seen.add(dedupe_key)
            hashtags.append(value)
        index = value_end

    return tuple(hashtags)


def _valid_hash_boundary(text: str, index: int) -> bool:
    if index == 0:
        return True
    previous = text[index - 1]
    return not (_is_hashtag_character(previous) or previous == "#")


def _is_hashtag_character(character: str) -> bool:
    return (
        character == "_"
        or character.isalnum()
        or unicodedata.category(character).startswith("M")
    )


__all__ = ["extract_hashtags"]
