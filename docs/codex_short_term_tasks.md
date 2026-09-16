# Codex Short-Term Tasks — Telegram Saved Messages Archive

This file is the active implementation backlog.

The tasks are ordered to minimize rework and keep each step independently testable. Codex should generally work from top to bottom unless a task is blocked.

---

## Phase 0 — Baseline and safety

### [ ] ST-00 — Inspect current project and preserve existing behavior

Goal: establish a safe baseline before refactoring.

Tasks:
- Inspect `main.py`, `getdata.py`, and current project assumptions.
- Record how the existing news-fetch workflow is invoked.
- Identify Telethon session handling, configuration inputs, output paths, and dependencies.
- Avoid changing existing runtime behavior in this task.

Acceptance criteria:
- Existing entry points are understood.
- Any duplicated imports / obvious cleanup opportunities may be noted, but not mixed into unrelated refactoring.
- A short note is added documenting current behavior and compatibility constraints.

Verification:
- Existing code imports successfully.
- If runnable credentials are unavailable, perform static validation only and report the limitation.

---

### [ ] ST-01 — Introduce project structure for archive code

Goal: separate Telegram access, archive logic, and existing podcast logic without overengineering.

Suggested structure:

```text
telegram_news_podcast/
├── telegram_client.py
├── saved_archive/
│   ├── __init__.py
│   ├── models.py
│   ├── fetch.py
│   ├── paths.py
│   ├── writer.py
│   └── state.py
```

Tasks:
- Create a minimal reusable module layout.
- Do not move every existing function immediately.
- Keep current entry points working.
- Add only dependencies actually required by the archive.

Acceptance criteria:
- Existing project remains runnable/importable.
- Archive code has a clear home.
- No NAS service, web UI, or gallery code is added.

---

## Phase 1 — Shared Telegram client

### [ ] ST-02 — Refactor reusable Telethon client/session creation

Goal: stop duplicating Telegram login/session logic.

Tasks:
- Extract client construction into a reusable helper.
- Support:
  - API ID
  - API hash
  - session path/name
  - timezone configuration
- Keep the session outside the archive root by design.
- Ensure existing channel-fetch code can reuse the helper.

Security requirement:
- Never write Telethon `.session` files into the NAS archive directory.
- Document a recommended local config path such as:
  `~/.config/telegram-news-podcast/`

Acceptance criteria:
- Existing channel fetching can use the shared client.
- Saved Messages code can use the same client.
- Session location is configurable and clearly separated from archive storage.

Verification:
- Import/static tests.
- If credentials are available, connect and resolve `me` successfully.

---

## Phase 2 — Saved Messages ingestion

### [ ] ST-03 — Implement Saved Messages iteration

Goal: retrieve Saved Messages as raw Telegram messages.

Tasks:
- Iterate Saved Messages using Telethon.
- Support:
  - full initial scan;
  - bounded test scan by limit;
  - chronological normalization.
- Capture raw identifiers required for later reconciliation.
- Do not download media yet.

Required fields:
- Telegram message ID
- saved timestamp
- edit timestamp, if any
- grouped/media-group ID
- reply metadata where available
- raw text/caption
- raw forward/source metadata required for source resolution

Acceptance criteria:
- A test run can list Saved Message IDs and timestamps.
- Message order is deterministic.
- Empty-text media messages are not skipped.

---

### [ ] ST-04 — Resolve Saved Messages tags

Goal: preserve Telegram Saved Messages tags independently from hashtags.

Tasks:
- Read reaction-tag / Saved Messages tag metadata exposed by Telegram.
- Resolve tag display names where available.
- Associate tags with each message.
- Preserve stable identifiers needed to detect later tag changes.

Acceptance criteria:
- Tagged and untagged messages can be distinguished.
- Saved tags are stored separately from message hashtags.
- Missing or unsupported tag metadata does not abort archiving.

Verification:
- Test at least one tagged and one untagged Saved Message when account data permits.

---

### [ ] ST-05 — Extract textual hashtags

Goal: preserve normal `#hashtag` usage in message text.

Tasks:
- Extract hashtags from text/captions.
- Keep original text unchanged.
- Store normalized hashtag values separately.
- Avoid treating Telegram Saved tags as hashtags.

Acceptance criteria:
- Hashtag extraction is deterministic.
- Unicode hashtags are handled reasonably.
- Duplicate hashtags within one message are deduplicated in metadata while original text remains untouched.

---

### [ ] ST-06 — Resolve forwarded/original source metadata

Goal: identify where Saved Messages came from when Telegram exposes this information.

Capture when available:
- source type: channel/group/user/self/hidden/unknown
- source peer ID
- display title/name
- username
- original message ID
- original message timestamp
- public `t.me` URL when constructible

Tasks:
- Handle normal channel forwards.
- Handle hidden/private source cases gracefully.
- Never discard a message because source resolution fails.
- Cache resolved peers during a run to avoid repeated API lookups.

Acceptance criteria:
- Normal forwarded channel messages show source title.
- Self-created Saved Messages are identified as self.
- Hidden/unknown cases are represented explicitly instead of failing.

---

## Phase 3 — Canonical archive format

### [ ] ST-07 — Implement archive path and filename rules

Goal: create a NAS/SMB-friendly filesystem layout.

Canonical layout:

```text
archive/YYYY/MM/DD/
├── YYYY-MM-DD.md
├── YYYY-MM-DD.jsonl
└── media/
```

Tasks:
- Implement path generation from `saved_at`.
- Add safe filename sanitization.
- Keep single-directory media counts bounded naturally by day.
- Media naming must include Telegram message ID.

Suggested media filename:

```text
HHMMSS_<message-id>_<source>_<type>_<index>.<ext>
```

Acceptance criteria:
- Invalid SMB/macOS/Windows filename characters are sanitized.
- Lengths are bounded.
- Collisions are handled deterministically.
- Message ID remains visible in media filenames.

---

### [ ] ST-08 — Define normalized archive record model

Goal: have one stable internal representation before writing files.

Minimum record fields:
- schema version
- Telegram message ID
- saved_at
- original_at
- edited_at
- text
- saved tags
- hashtags
- source metadata
- grouped ID
- reply metadata
- media metadata
- archive-relative paths
- status fields needed for later reconciliation

Tasks:
- Implement as dataclass / TypedDict / equivalent.
- Keep serialization stable.
- Avoid embedding Telethon objects directly in canonical JSON.

Acceptance criteria:
- A Telegram message can be normalized without writing to disk.
- Normalized objects serialize cleanly to JSON.

---

### [ ] ST-09 — Write daily JSONL archive

Goal: establish machine-readable canonical metadata.

Tasks:
- Write one JSON object per logical archive item.
- Preserve UTF-8 text directly.
- Make writes crash-safe:
  - write temporary file;
  - fsync/close;
  - atomic replace where practical.
- Rebuild a day deterministically rather than blindly appending duplicates.

Acceptance criteria:
- Rerunning the same input does not duplicate entries.
- JSONL remains valid after rebuild.
- Records are ordered consistently.

---

### [ ] ST-10 — Write daily Markdown archive

Goal: make the archive readable directly over SMB/Finder.

Include:
- saved time
- original time when available
- Telegram message ID
- source
- source username
- original message ID
- Saved tags
- hashtags
- message text
- media relative paths
- original URL when available

Tasks:
- Render one daily Markdown file.
- Group media albums logically.
- Preserve messages with no text.
- Keep formatting simple and portable.

Acceptance criteria:
- Opening the file in a normal text/Markdown viewer is enough to understand the day's Saved Messages.
- Reruns reproduce the same content deterministically.

---

## Phase 4 — Media

### [ ] ST-11 — Download original media

Goal: archive Telegram media in ordinary files.

Tasks:
- Download photos, videos, documents, audio/voice, stickers, and other supported media.
- Preserve original extension where possible.
- Preserve original document filename in metadata.
- Do not transcode.
- Do not package files into ZIP or proprietary blobs.
- Track download failures without aborting the entire sync.

Acceptance criteria:
- Media files are directly openable from SMB/Finder.
- JSONL/Markdown link to the correct relative paths.
- Existing verified media is not re-downloaded unnecessarily.

---

### [ ] ST-12 — Handle albums / grouped media

Goal: preserve album relationships without creating per-message directories.

Tasks:
- Detect shared grouped IDs.
- Keep album media in the day's `media/` folder.
- Preserve media order.
- Render album members together in Markdown.
- Store grouped ID in JSONL/SQLite.

Acceptance criteria:
- A multi-photo/video Telegram album remains recognizable as one logical group.

---

## Phase 5 — Incremental sync and recovery

### [ ] ST-13 — Implement sync state

Goal: support efficient repeated syncs.

Create a state file such as:

`metadata/sync-state.json`

Track enough information for:
- newest successfully processed message;
- incomplete media downloads;
- schema version;
- last successful sync time;
- recent reconciliation window marker.

Do not rely on a single `last_message_id` as the only state.

Acceptance criteria:
- Re-running after success fetches only necessary new/recent data.
- Interrupted runs can recover without corrupting the archive.
- State is updated only after corresponding archive writes succeed.

---

### [ ] ST-14 — Implement recent-message reconciliation

Goal: detect changes to recent Saved Messages.

Detect where practical:
- changed Saved tags;
- edited text;
- changed source metadata;
- newly available media;
- messages deleted from Telegram.

Policy:
- Never automatically delete already archived local data.
- Mark Telegram deletion status in metadata instead.

Acceptance criteria:
- A tag change can update the canonical day record.
- Deleted Telegram messages remain locally archived.

---

### [ ] ST-15 — Add retry and failure reporting

Goal: make long archival runs reliable.

Tasks:
- Retry transient Telegram/media download failures with bounded backoff.
- Record permanent failures.
- Continue processing unrelated messages.
- Produce a concise end-of-run summary.

Required report fields:
- messages scanned
- messages added
- messages updated
- media downloaded
- media reused/skipped
- failed media
- unresolved sources
- days rewritten

Acceptance criteria:
- One failed media item does not abort a full sync.
- Failures are visible and actionable.

---

## Phase 6 — SQLite index

### [ ] ST-16 — Implement rebuildable SQLite index

Goal: make local search fast without making SQLite canonical.

Suggested tables:
- messages
- media
- sources
- saved_tags
- message_saved_tags
- hashtags
- message_hashtags
- links

Tasks:
- Build/update the index from normalized archive records.
- Keep archive-relative paths.
- Add useful indexes on date/source/tag/media type.

Acceptance criteria:
- Deleting the SQLite DB and rebuilding from JSONL produces equivalent searchable content.
- SQLite failure does not invalidate canonical archive files.

---

### [ ] ST-17 — Add SQLite FTS5 text search

Goal: allow fast full-text search.

Tasks:
- Create FTS index for message text.
- Keep FTS rebuildable.
- Document a few example queries.

Acceptance criteria:
- Search by keyword returns matching Saved Messages quickly.
- FTS remains an optional derived index.

---

## Phase 7 — CLI and usability

### [ ] ST-18 — Add a small archive CLI

Goal: make Codex/users able to run and report tasks consistently.

Suggested commands:

```text
python -m ... saved-archive sync
python -m ... saved-archive sync --limit 100
python -m ... saved-archive reconcile
python -m ... saved-archive rebuild-index
python -m ... saved-archive status
```

Tasks:
- Keep CLI minimal.
- Support configurable archive root.
- Print concise structured summaries.

Acceptance criteria:
- Core archive workflow does not require editing Python source.
- Commands are documented.

---

### [ ] ST-19 — Add tests for deterministic archive behavior

Minimum test coverage:
- filename sanitization
- source normalization
- hashtag extraction
- tagged vs untagged records
- daily grouping
- album grouping
- JSONL round trip
- Markdown deterministic rendering
- duplicate rerun behavior
- state update safety

Use fixtures/mocks so most tests do not require a live Telegram account.

Acceptance criteria:
- Core archive logic can be validated offline.
- Live-account tests, if any, are optional/manual.

---

### [ ] ST-20 — End-to-end V1 validation

Goal: prove the V1 workflow before adding convenience features.

Test with a bounded sample containing, where available:
- self text
- forwarded channel text
- tagged Saved Message
- untagged Saved Message
- photo
- video
- document
- album
- edited message
- source that cannot be fully resolved

Validate:
- daily folder layout
- Markdown readability
- JSONL validity
- media paths
- SQLite rebuild
- incremental rerun behavior
- no session file inside archive root

Completion condition:
- V1 is considered usable over SMB/Finder.
- Only then should V1.5 items be considered.

---

## Short-term exit criteria

Short-term work is complete when:

1. Saved Messages can be archived incrementally.
2. Canonical data is ordinary Markdown, JSONL, and original media.
3. Source/tag/date/media metadata is preserved.
4. Archive is readable over SMB without a special app.
5. SQLite can be deleted and rebuilt.
6. NAS does not need a permanent background service.
7. Existing TelegramNewsPodcast functionality still works or has a documented migration.
8. An end-of-run report clearly states what changed and what failed.
