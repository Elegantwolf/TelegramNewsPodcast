"""Saved Messages archive components.

The submodules are kept separate so fetching, normalization, filesystem path
rules, writing, and sync state can be tested independently.
"""

__all__ = ["models", "fetch", "paths", "writer", "state"]
