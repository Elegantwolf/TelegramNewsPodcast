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
- Validate against the real Telegram account in small read-only stages instead of waiting until the end of V1.

## Current audited status

Last audited against `main`: **2026-09-16**, after commit `8e7be8a` (`docs: update archive task status`).

Completed implementation tasks:
- **ST-00, ST-01, ST-02, ST-02A, ST-03, ST-04, ST-05**

Current implementation target:
- **ST-06 — Resolve forwarded/original source metadata**

Validation status:
- **REAL-00 — live login smoke test: pending**
- **REAL-01 — real Saved Messages metadata smoke test: pending**
- No real-account validation has yet been recorded in the repository.

Implemented Saved archive components:
- `fetch.py`
- `tags.py`
- `hashtags.py`

Intentional skeletons awaiting later tasks:
- `models.py`
- `paths.py`
- `writer.py`
- `state.py`

## Real-account validation gates

The project now uses staged real validation:

```text
REAL-00  Login only
    ↓
ST-06    Source resolver
    ↓
REAL-01  20–50 message metadata smoke test, read-only
    ↓
ST-07..10
    ↓
REAL-02  Local Markdown/JSONL archive smoke test
    ↓
ST-11..12
    ↓
REAL-03  Local media smoke test
    ↓
Reliability/index/CLI/E2E
    ↓
Production NAS full sync
```

Rules:
- REAL-01 does not download media.
- REAL-02/REAL-03 use local temporary storage first, not the production NAS archive.
- The NAS/SMB path is promoted to production only after local smoke tests pass.
- Telegram sessions remain outside the archive root.
- Real validation should cover Saved tags, hashtags, source metadata, media-only messages, albums, and private/hidden/unresolved forward cases where available.

## Current priority

1. Complete **REAL-00** if the local environment/account is ready.
2. Implement **ST-06** source resolution.
3. Run **REAL-01** against 20–50 real Saved Messages.
4. Only after metadata assumptions are confirmed, implement ST-07/ST-08 and freeze the canonical schema.

The broader V1 goal remains:

- read Saved Messages with Telethon;
- preserve text, tags, hashtags, source metadata, times, albums, and original media;
- write a daily SMB-friendly archive;
- support safe incremental synchronization;
- create a rebuildable SQLite index;
- later expose normalized data to TelegramNewsPodcast.

## Status convention

- `[ ]` Not started
- `[~]` In progress
- `[x]` Completed
- `[!]` Blocked
- `[-]` Intentionally deferred / not required

When Codex completes a task or validation gate, update the checkbox and add a concise completion note.

## Completion note format

```text
Completed:
- What changed
- Main files changed
- Tests / verification performed
- Any migration or compatibility impact

Remaining:
- Follow-up items

Risks / Notes:
- Anything the next session must know
```

## Session report format

```text
Session summary
- Completed tasks:
- Completed validation gates:
- Partially completed tasks:
- Files changed:
- Validation performed:
- Known issues:
- Recommended next task:
```

## Scope guard

Before implementing anything from the long-term roadmap, verify that:

1. prerequisite short-term tasks are complete;
2. staged real-account validation has not exposed unresolved schema assumptions;
3. the feature solves an observed need;
4. it does not interfere with NAS HDD sleep without explicit approval;
5. it remains rebuildable from canonical archive data where possible.
