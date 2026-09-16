"""Saved Messages archive components.

The submodules are kept separate so fetching, normalization, filesystem path
rules, writing, and sync state can be tested independently.
"""

from .fetch import RawSavedMessage, fetch_saved_messages, iter_saved_messages
from .hashtags import extract_hashtags
from .tags import (
    SavedMessageTag,
    SavedTagCatalog,
    extract_saved_tags,
    fetch_saved_tag_catalog,
)

__all__ = [
    "RawSavedMessage",
    "fetch_saved_messages",
    "iter_saved_messages",
    "extract_hashtags",
    "SavedMessageTag",
    "SavedTagCatalog",
    "extract_saved_tags",
    "fetch_saved_tag_catalog",
    "tags",
    "models",
    "fetch",
    "paths",
    "writer",
    "state",
]
