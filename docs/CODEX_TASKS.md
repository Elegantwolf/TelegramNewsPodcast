# Codex Task Overview

This document is the entry point for Codex when working on the Telegram Saved Messages archive integration.

## Read first

1. `docs/telegram_saved_archive_plan.md`
2. `docs/codex_short_term_tasks.md`
3. `docs/codex_long_term_tasks.md`

The archive plan defines the target architecture. The short-term task file contains the implementation sequence that should be worked on now. The long-term task file contains deferred work that must not be pulled forward unless its prerequisites are met.

## Working principle

- Keep the archive simple and human-readable.
- Prefer ordinary files over proprietary containers.
- Do not introduce always-on NAS services for V1.
- Do not expand scope into a full media-management application.
- Reuse existing Telethon code where reasonable, but refactor shared Telegram client/session logic instead of copying it.
- Preserve backward compatibility with the existing news-podcast workflow unless a task explicitly authorizes a breaking change.

## Current priority

The current priority is to build a reliable Saved Messages archive pipeline that:

- reads Saved Messages with Telethon;
- preserves text, tags, hashtags, source metadata, times, albums, and original media;
- writes a daily SMB-friendly archive;
- supports safe incremental synchronization;
- creates a rebuildable SQLite index;
- can later act as a normalized data source for TelegramNewsPodcast.

## Status convention

Use the following markers in task documents:

- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed
- `[!]` Blocked
- `[-]` Intentionally deferred / not required

When Codex completes a task, update the checkbox and add a short completion note directly below that task.

## Completion note format

Use this compact format:

```text
Completed:
- What changed
- Main files changed
- Tests / verification performed
- Any migration or compatibility impact

Remaining:
- Follow-up items, if any

Risks / Notes:
- Anything the next session must know
```

## Session report format

At the end of each Codex work session, report:

```text
Session summary
- Completed tasks:
- Partially completed tasks:
- Files changed:
- Validation performed:
- Known issues:
- Recommended next task:
```

Keep reports factual and concise. Do not restate the entire roadmap.

## Scope guard

Before implementing anything from the long-term roadmap, verify that:

1. all prerequisite short-term tasks are complete;
2. the feature solves an observed need rather than a hypothetical one;
3. it does not interfere with NAS HDD sleep without explicit approval;
4. it remains rebuildable from canonical archive data where possible.
