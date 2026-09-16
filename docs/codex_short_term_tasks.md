# Codex Short-Term Tasks — Telegram Saved Messages Archive

This file is the active implementation backlog.

The tasks are ordered to minimize rework and keep each step independently testable. Codex should generally work from top to bottom unless a task is blocked.

---

## Validation strategy

Real Telegram validation is intentionally staged instead of being postponed until ST-20.

Validation levels:

1. **Level 1 — Login smoke test**
   - Establish a real user-session connection.
   - Resolve `get_me()`.
   - Do not fetch/archive content yet.

2. **Level 2 — Metadata smoke test**
   - Fetch a small bounded sample (target: 20–50 Saved Messages).
   - Verify Saved tags, hashtags, source metadata, timestamps, albums/media-only messages, and hidden/private forward edge cases.
   - Do not download media.

3. **Level 3 — Archive/media smoke tests**
   - First write Markdown/JSONL to a temporary local archive.
   - Then download a small media sample.
   - Only after successful local validation should a NAS/SMB path be used as the production archive root.

The real account is used only as a read-only validation source until media-download tasks explicitly begin.

---

## Phase 0 — Baseline and safety

### [x] ST-00 — Inspect current project and preserve existing behavior

Goal: establish a safe baseline before refactoring.

Completed:
- Confirmed `main.py` is the current entry point and calls the asynchronous `getdata()` workflow.
- Confirmed `getdata.py` authenticates through Telethon, resolves one configured channel, fetches text messages in a local-time window, and writes a dated channel JSON file.
- Existing runtime behavior was preserved during the baseline audit.
- Syntax compilation passed in the recorded Codex environment.

---

### [x] ST-01 — Introduce project structure for archive code

Goal: separate Telegram access, archive logic, and existing podcast logic without overengineering.

Completed:
- Added the `telegram_news_podcast/` package and `saved_archive/` subpackage.
- Added module boundaries for client access, fetching, models, paths, writing, and sync state.
- Existing root-level entry points remain available.

---

## Phase 1 — Shared Telegram client

### [x] ST-02 — Refactor reusable Telethon client/session creation

Goal: stop duplicating Telegram login/session logic.

Completed:
- Added `TelegramClientConfig` and `create_telegram_client()`.
- Existing channel fetching uses the shared factory.
- Session location is configurable and documented outside the NAS archive.

---

### [x] ST-02A — Remove committed Telegram credentials and add repository secret hygiene

Priority: **P0 / mandatory before live Saved Messages testing**

Completed:
- Removed live API credentials from tracked source.
- Added environment-variable configuration.
- Added `.env.example`.
- Added `.gitignore` coverage for secrets, Telegram session files, generated archive/output data, SQLite/cache files, and Python caches.
- Default session location is local: `~/.config/telegram-news-podcast/telegram.session`.

Risks / Notes:
- Credentials previously committed to public Git history should be treated as exposed.
- Repository changes do not erase old Git history; credential invalidation/rotation is an owner action.
- Never reproduce exposed values in reports or documentation.

---

### [ ] REAL-00 — Live login smoke test

Type: **Validation gate / Level 1**

Goal: prove that the shared Telegram client can authenticate against the real account before relying exclusively on mocks.

Tasks:
- Ensure a reproducible local Python environment exists.
- Record supported Python version.
- Add a minimal dependency declaration before or as part of this task (for example `requirements.txt` or `pyproject.toml`) containing the runtime dependencies needed for the current code, at minimum Telethon and pytz if still required.
- Create or expose a minimal login-validation path that:
  - constructs the shared Telegram client from external configuration;
  - opens the existing/new local session;
  - calls `get_me()`;
  - prints only non-secret account/session status.
- Do not fetch Saved Messages in this gate.
- Do not write anything to NAS storage.

Acceptance criteria:
- A clean local environment can install the declared dependencies.
- Real Telegram authentication succeeds.
- `get_me()` resolves the intended account.
- The session is stored outside the archive root.
- No credential value is printed or written into tracked files.

Report:
- Python version
- Telethon version
- login success/failure
- session path (path only, no session contents)
- any 2FA/login edge case encountered

---

## Phase 2 — Saved Messages ingestion

### [x] ST-03 — Implement Saved Messages iteration

Goal: retrieve Saved Messages as raw Telegram messages.

Completed:
- Implemented `RawSavedMessage`, `fetch_saved_messages()`, and `iter_saved_messages()`.
- Supports full scans and bounded scans.
- Preserves media-only messages.
- Captures message ID, saved/edit timestamps, grouped ID, reply metadata, text/caption, and raw forward/source metadata.
- Deterministic chronological sorting is implemented.

Risks / Notes:
- Current full-scan implementation buffers records before sorting; revisit for large archives during incremental-sync work.

---

### [x] ST-04 — Resolve Saved Messages tags

Goal: preserve Telegram Saved Messages tags independently from hashtags.

Completed:
- Added Saved Message tag/catalog models and best-effort Telegram tag catalog retrieval.
- Supports emoji/custom-emoji identities, display names/titles, counts, chosen order, and catalog hash.
- Unsupported/missing metadata degrades gracefully.

---

### [x] ST-05 — Extract textual hashtags

Goal: preserve ordinary `#hashtag` values separately from Saved tags.

Completed:
- Added deterministic Unicode-aware hashtag extraction.
- Original message text remains untouched.
- Duplicate hashtags are normalized for metadata while preserving first-seen spelling.

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

### [ ] REAL-01 — Live Saved Messages metadata smoke test

Type: **Validation gate / Level 2**

Depends on:
- REAL-00
- ST-03
- ST-04
- ST-05
- ST-06

Goal: validate the real Telegram metadata model before freezing the normalized archive schema.

Run shape:
- Use the real Telegram user account.
- Read only a bounded sample, target **20–50 Saved Messages**.
- Do **not** download media.
- Do **not** modify Telegram messages, tags, or reactions.
- Do **not** write to NAS.

Preferred command shape (exact CLI may be implemented later):

```text
python -m telegram_news_podcast saved-archive inspect --limit 50
```

Required validation coverage where available:
- self-authored Saved Message text
- forwarded public-channel message
- tagged Saved Message
- untagged Saved Message
- message containing ordinary hashtag(s)
- photo/media-only message
- video/document metadata if present
- album/grouped media
- edited message
- private/hidden/unresolved forward source

Required summary:
- account identifier (non-secret)
- messages fetched
- text-only/media message counts
- tagged vs untagged count
- unique Saved tags
- hashtag-bearing message count
- source counts by type
- grouped/album count
- unresolved source count
- parsing failures/warnings

Spot-check output:
- Print a small number of representative normalized/raw records.
- Truncate long message text.
- Never print secrets/session contents.

Acceptance criteria:
- Real Saved Messages can be read successfully.
- Saved tags match Telegram UI for sampled tagged messages.
- Ordinary hashtags remain separate from Saved tags.
- Normal forwarded channel names/IDs/message IDs resolve correctly.
- Self messages are classified correctly.
- Hidden/private/unresolved sources fail gracefully.
- Media-only messages are retained.
- Album/grouped IDs behave as expected.
- Any mismatch between real Telethon objects and mock assumptions is documented before ST-07/ST-08 proceed.

Decision gate:
- **Do not freeze the normalized archive schema until REAL-01 passes or known discrepancies are explicitly documented and accepted.**

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
- Bound filename lengths.
- Handle collisions deterministically.
- Ensure media filenames include Telegram message ID.

Suggested media filename:

```text
HHMMSS_<message-id>_<source>_<type>_<index>.<ext>
```

---

### [ ] ST-08 — Define normalized archive record model

Goal: create the stable internal representation used by canonical writers.

Minimum fields:
- schema version
- Telegram message ID
- saved_at
- original_at
- edited_at
- text
- Saved tags
- hashtags
- source metadata
- grouped ID
- reply metadata
- media metadata
- archive-relative paths
- status/reconciliation fields

Requirements:
- Plain serializable values only.
- No Telethon objects in canonical JSON.
- Incorporate findings from REAL-01 before schema is treated as stable.

---

### [ ] ST-09 — Write daily JSONL archive

Goal: establish machine-readable canonical metadata.

Requirements:
- One JSON object per logical archive item.
- UTF-8.
- Deterministic ordering.
- Crash-safe rewrite using temp file + atomic replace where practical.
- Re-running the same input must not duplicate records.

---

### [ ] ST-10 — Write daily Markdown archive

Goal: make each day human-readable through SMB/Finder.

Include:
- saved/original times
- Telegram message ID
- source title/username/type
- original message ID/URL where available
- Saved tags
- hashtags
- message text
- media relative paths
- album grouping

Requirements:
- Preserve messages with no text.
- Deterministic rendering.
- Keep formatting simple and portable.

---

### [ ] REAL-02 — Local archive smoke test

Type: **Validation gate / Level 3A**

Depends on:
- REAL-01
- ST-07
- ST-08
- ST-09
- ST-10

Goal: validate canonical Markdown/JSONL with real data before using NAS storage.

Run shape:
- Use a bounded real-account sample (target 20–50 messages).
- Archive root must be a temporary/local path such as `/tmp/TelegramSavedTest` or a local project test directory excluded by Git.
- Do not download original media yet unless a later task explicitly enables it.
- Do not use the production NAS archive root.

Validate:
- expected `archive/YYYY/MM/DD/` layout
- daily Markdown readability
- JSONL validity
- UTF-8/CJK/emoji rendering
- chronological ordering
- Saved tags
- hashtags
- source names and original IDs
- media-only message placeholders/metadata
- albums/grouped relationships
- deterministic re-run behavior

Acceptance criteria:
- Human inspection of Markdown is satisfactory.
- JSONL can be parsed cleanly.
- Re-running produces equivalent canonical content without duplicate records.
- No Telegram session/credential file appears inside archive root.

Decision gate:
- Only after REAL-02 passes may NAS/SMB be used for canonical archive testing.

---

## Phase 4 — Media

### [ ] ST-11 — Download original media

Goal: archive Telegram media in ordinary files.

Tasks:
- Download photos, videos, documents, audio/voice, stickers, and supported media.
- Preserve original extension where possible.
- Preserve original document filename in metadata.
- Do not transcode.
- Do not package files into proprietary blobs.
- Track failures without aborting the entire run.
- Avoid re-downloading already verified media unnecessarily.

---

### [ ] ST-12 — Handle albums / grouped media

Goal: preserve album relationships without creating per-message directories.

Tasks:
- Detect shared grouped IDs.
- Keep media in the day's `media/` directory.
- Preserve member order.
- Render album members together in Markdown.
- Store grouped ID in canonical metadata and later SQLite.

---

### [ ] REAL-03 — Local media smoke test

Type: **Validation gate / Level 3B**

Depends on:
- REAL-02
- ST-11
- ST-12

Goal: validate a small real-media archive before any full sync or production NAS run.

Run shape:
- Use a small bounded real-account sample.
- Download media to a temporary/local archive.
- Prefer a sample containing:
  - photo
  - video
  - document/PDF
  - media-only message
  - album/grouped media

Validate:
- downloaded files open normally in Finder/standard applications
- filename sanitization
- message ID present in filenames
- original filename preservation for documents
- correct extension/MIME metadata
- Markdown/JSONL relative paths
- album member ordering
- re-run skips/reuses already verified files as designed

Acceptance criteria:
- Sample media is directly human-readable/openable.
- No transcoding or proprietary packaging is required.
- Canonical text metadata links to the correct files.
- Re-run behavior does not create duplicate media unnecessarily.

Decision gate:
- Only after REAL-03 passes should a full-history media sync or production NAS archive root be attempted.

---

## Phase 5 — Incremental sync and recovery

### [ ] ST-13 — Implement sync state

Goal: support efficient repeated syncs.

Create:
`metadata/sync-state.json`

Track enough information for:
- newest successfully processed message
- incomplete media downloads
- schema version
- last successful sync time
- reconciliation marker/window

Requirements:
- Do not rely solely on `last_message_id`.
- State updates occur only after corresponding canonical writes succeed.
- Interrupted runs recover safely.

---

### [ ] ST-14 — Implement recent-message reconciliation

Goal: detect changes to recent Saved Messages.

Detect where practical:
- changed Saved tags
- edited text
- changed source metadata
- newly available media
- deleted-from-Telegram status

Policy:
- Never automatically delete already archived local data.
- Mark remote deletion status instead.

---

### [ ] ST-15 — Add retry and failure reporting

Goal: make long archive runs reliable.

Report:
- messages scanned
- messages added
- messages updated
- media downloaded
- media reused/skipped
- failed media
- unresolved sources
- days rewritten

Requirements:
- transient failures use bounded retry/backoff
- one failed media item does not abort unrelated work
- permanent failures remain visible/actionable

---

## Phase 6 — SQLite index

### [ ] ST-16 — Implement rebuildable SQLite index

Goal: fast local querying while keeping ordinary files canonical.

Suggested tables:
- messages
- media
- sources
- saved_tags
- message_saved_tags
- hashtags
- message_hashtags
- links

Acceptance criteria:
- Database can be deleted and rebuilt from canonical archive data.
- SQLite failure cannot invalidate the Markdown/JSONL/media archive.

---

### [ ] ST-17 — Add SQLite FTS5 text search

Goal: fast full-text search over message text.

Requirements:
- FTS index remains rebuildable/derived.
- Document a few representative queries.

---

## Phase 7 — CLI and usability

### [ ] ST-18 — Add a small archive CLI

Goal: make archive workflows runnable without editing Python source.

Target command family:

```text
python -m ... validate-login
python -m ... saved-archive inspect --limit 50
python -m ... saved-archive sync
python -m ... saved-archive sync --limit 100
python -m ... saved-archive reconcile
python -m ... saved-archive rebuild-index
python -m ... saved-archive status
```

Notes:
- A minimal temporary command/helper may be implemented earlier to satisfy REAL-00/REAL-01; ST-18 later consolidates the user-facing CLI.
- Support configurable archive root.
- Print concise structured summaries.

---

### [ ] ST-19 — Add tests for deterministic archive behavior

Minimum coverage:
- filename sanitization
- source normalization
- hashtag extraction
- Saved tag association
- tagged vs untagged records
- daily grouping
- album grouping
- JSONL round trip
- Markdown deterministic rendering
- duplicate rerun behavior
- state update safety

Principle:
- Add focused regression tests earlier when a task introduces pure parsing/normalization logic; ST-19 is the point where coverage is completed and organized, not the first time tests are allowed.

---

### [ ] ST-20 — End-to-end V1 validation

Goal: prove the complete V1 workflow after the staged real-account smoke tests.

Test with a bounded sample containing where available:
- self text
- forwarded channel text
- tagged and untagged messages
- photo
- video
- document
- album
- edited message
- unresolved/hidden source

Validate:
- canonical daily layout
- Markdown
- JSONL
- original media
- SQLite rebuild
- incremental rerun
- reconciliation
- failure reporting
- no session/credential inside archive root
- SMB/Finder usability

Completion condition:
- V1 is usable as a normal-file NAS archive.
- Only then should V1.5 gallery/thumbnail conveniences be considered.

---

## Production NAS gate

A production NAS/SMB archive root should not be used for the first validation run.

Promotion sequence:

```text
REAL-00  real login
   ↓
ST-03..06 metadata capabilities
   ↓
REAL-01  real metadata smoke test
   ↓
ST-07..10 canonical text archive
   ↓
REAL-02  local archive smoke test
   ↓
ST-11..12 media
   ↓
REAL-03  local media smoke test
   ↓
ST-13..20 reliability/index/CLI/E2E
   ↓
Production NAS full sync
```

For initial production rollout:
- Prefer first full canonical sync on local storage if capacity permits.
- Inspect representative files.
- Then copy/sync to NAS or explicitly switch archive root to the SMB mount.
- Never store Telegram login sessions in the NAS archive tree.

---

## Short-term exit criteria

Short-term work is complete when:

1. Real-account login and staged smoke tests pass.
2. Saved Messages can be archived incrementally.
3. Canonical data is ordinary Markdown, JSONL, and original media.
4. Source/tag/date/media metadata is preserved.
5. Archive is readable over SMB without a special app.
6. SQLite can be deleted and rebuilt.
7. NAS requires no permanent background service.
8. Existing TelegramNewsPodcast functionality still works or has a documented migration.
9. End-of-run reports clearly state what changed and what failed.
