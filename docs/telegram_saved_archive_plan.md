# Telegram Saved Messages Local Archive Plan

## 1. Purpose

This document defines a lightweight, long-term archive design for Telegram **Saved Messages**.

The archive is intended to serve two roles:

1. A standalone, human-readable personal archive that can live on a NAS and be browsed over SMB.
2. A reusable data-ingestion / dependency layer for `TelegramNewsPodcast`, so later news-processing or podcast-generation code can consume normalized Telegram messages instead of implementing Telegram access repeatedly.

The main design principle is:

> Keep the canonical archive as ordinary files that remain readable without the application. Indexes, databases, thumbnails, and HTML views are optional and rebuildable.

The design deliberately avoids turning the project into a full photo-management application or a permanently running NAS service.

---

## 2. Goals

### Required

- Export all Saved Messages incrementally.
- Preserve message text.
- Preserve Telegram Saved Messages tags.
- Preserve normal hashtags contained in message text.
- Preserve media in original downloadable formats.
- Preserve the original source of forwarded messages whenever Telegram exposes it.
- Preserve source/channel name, username, peer ID, and original message ID when available.
- Preserve both saved time and original message time when available.
- Work well on a NAS accessed through SMB.
- Keep the archive human-readable without proprietary containers.
- Avoid huge directories and huge numbers of per-message folders.
- Work without requiring a continuously running web/database service on the NAS.
- Allow the NAS HDD to sleep normally when the archive is not being accessed.
- Support incremental synchronization.
- Keep Telegram authentication/session files outside the NAS archive.

### Nice to have

- SQLite search index.
- Static HTML gallery/index.
- Lightweight thumbnails for images and videos.
- Grouping/search by source, date, tag, hashtag, and media type.
- Random image/video browsing.
- Duplicate detection.
- Later integration with the news/podcast pipeline.

### Explicit non-goals for V1

- Immich/PhotoPrism-style media management.
- Always-running FastAPI/Flask/backend services on the NAS.
- OCR.
- AI classification / automatic tagging.
- Video transcoding.
- PDF full-text extraction.
- Complex browser UI.
- Replacing Telegram itself as a message client.

---

## 3. Relationship to TelegramNewsPodcast

The existing project already uses Telethon in `getdata.py` to retrieve Telegram channel messages.

The Saved Messages archive should therefore be implemented as a lower-level Telegram data layer rather than an unrelated application.

Possible future architecture:

```text
Telegram API / Telethon
        |
        +--------------------+
        |                    |
        v                    v
Saved Messages Archive   Channel Fetcher
        |                    |
        +---------+----------+
                  |
                  v
         Normalized Messages
                  |
                  v
       News / Podcast Pipeline
```

Where practical, Telegram client/session/configuration code should eventually be shared instead of duplicated between the archive and the current channel-fetching logic.

---

## 4. Storage Strategy

### Core rule

Do **not** create one folder per Telegram message.

A per-message directory hierarchy would create a very large number of small directories and is undesirable for long-term SMB/NAS browsing.

Instead:

> Use one archive directory per day.

Example:

```text
TelegramSaved/
├── README.md
├── archive/
│   └── 2026/
│       └── 09/
│           └── 16/
│               ├── 2026-09-16.md
│               ├── 2026-09-16.jsonl
│               └── media/
│                   ├── 201503_123456_NASA_photo_01.jpg
│                   ├── 201503_123456_NASA_video_01.mp4
│                   ├── 202144_123457_self_document_01.pdf
│                   └── ...
├── database/
│   └── archive.sqlite
├── metadata/
│   ├── tags.json
│   ├── sources.json
│   └── sync-state.json
└── optional/
    ├── gallery/
    └── thumbnails/
```

The exact root path must be configurable so the archive can be written directly to a mounted SMB path or synchronized to the NAS later.

---

## 5. Daily Markdown File

Each day gets one human-readable Markdown file.

Example:

```markdown
# Saved Messages — 2026-09-16

## 20:15:03 — NASA

Telegram ID: 123456  
Saved: 2026-09-16 20:15:03 JST  
Original: 2026-09-16 18:42:10 JST  
Source: NASA  
Source Type: channel  
Source Username: @NASA  
Original Message ID: 98765  
Saved Tags: Space, Research  
Hashtags: #Artemis

Message text here...

Attachments:
- media/201503_123456_NASA_photo_01.jpg

Original URL:
https://t.me/NASA/98765

---

## 20:21:44 — Self

Telegram ID: 123457  
Saved: 2026-09-16 20:21:44 JST  
Saved Tags: none

Personal note here.
```

The Markdown file exists primarily for:

- SMB/Finder browsing.
- Future-proof human readability.
- Simple text search.
- Disaster recovery if all indexes are lost.

It is not the authoritative machine database.

---

## 6. Daily JSONL File

Each day also gets one JSONL file:

```text
2026-09-16.jsonl
```

One JSON object per logical message/archive item.

Example:

```json
{"id":123456,"saved_at":"2026-09-16T20:15:03+09:00","original_at":"2026-09-16T18:42:10+09:00","source":{"type":"channel","id":1234,"title":"NASA","username":"NASA","message_id":98765},"saved_tags":["Space","Research"],"hashtags":["Artemis"],"text":"...","media":["media/201503_123456_NASA_photo_01.jpg"]}
```

Why JSONL instead of one JSON file per message:

- Far fewer small files.
- Human-readable.
- Streamable.
- Append/update tooling is simple.
- Can rebuild SQLite later.
- Easy to inspect with command-line tools.

JSONL and media are canonical archive data.

---

## 7. Metadata Model

Keep the following concepts separate.

### 7.1 Saved Messages tags

Telegram Saved Messages reaction-tags / saved tags.

Examples:

```text
AI
Photography
Paper
```

Store as a dedicated field:

```text
saved_tags
```

### 7.2 Hashtags

Hashtags literally present in message text:

```text
#AI
#Japan
#OpenAI
```

Store separately:

```text
hashtags
```

### 7.3 Source

The original source of a forwarded/saved message.

Examples:

```text
NASA
Reuters
A Telegram channel
A private group
A user
Self
Hidden sender
Unknown
```

Store separately:

```text
source_type
source_id
source_title
source_username
source_message_id
```

Do not collapse source names into Saved Messages tags internally.

A UI/index may expose a synthetic filter such as `source:NASA`, but the underlying data model should remain separate.

---

## 8. Forwarded Message Source Handling

For normal forwarded messages, Telegram may expose the original peer and original message ID.

When available, save:

- Source type.
- Source peer ID.
- Channel/group/user display name.
- Username.
- Original message ID.
- Original message timestamp.
- Original public Telegram URL when one can be constructed.

Example filename component:

```text
201503_123456_NASA_photo_01.jpg
```

This makes media files understandable even when copied outside the archive.

### Edge cases

Source information is not guaranteed to be complete.

Possible source states:

```text
channel
group
user
self
hidden
unknown
```

If Telegram exposes only a display name because of forwarding privacy, preserve that text rather than dropping the source entirely.

Never discard a Saved Message because source resolution fails.

---

## 9. Time Handling

Preserve both:

```text
saved_at
original_at
```

`saved_at` controls the archive path:

```text
archive/YYYY/MM/DD/
```

`original_at` is metadata used for searching and provenance.

Timezone should be explicit and configurable. Default can be `Asia/Tokyo`.

---

## 10. Media Handling

Download original Telegram media without transcoding when possible.

Examples:

- JPEG / PNG / WebP
- MP4 / MOV
- PDF
- ZIP
- Office files
- OGG/voice messages
- Stickers

Do not automatically convert originals to WebP, H.265, archives, or other opaque formats.

Suggested naming convention:

```text
HHMMSS_<telegram-message-id>_<source>_<type>_<index>.<ext>
```

Examples:

```text
201503_123456_NASA_photo_01.jpg
201503_123456_NASA_video_01.mp4
202144_123457_self_document_01.pdf
```

Filename sanitization must:

- Remove filesystem-invalid characters.
- Bound total filename length.
- Preserve the Telegram message ID.
- Preserve the original extension.
- Optionally preserve a sanitized original document filename.

---

## 11. Albums / Grouped Media

Telegram media albums should be recognized through their grouped/media-group identifier.

For the daily archive, do not create a directory per album.

Instead:

- Keep individual media files in the day's `media/` directory.
- Store the common grouped ID in JSONL/SQLite.
- Render the corresponding messages/media together in Markdown or later gallery views.

---

## 12. Untagged Messages

Untagged messages are first-class archive items.

Do not dump them into a separate giant physical directory.

They remain in their normal date archive.

Record:

```text
saved_tags = []
```

An optional generated index may expose:

```text
Untagged
Untagged from channels
Untagged images
Untagged videos
Untagged documents
```

These are logical views, not duplicated physical media.

---

## 13. SQLite Index

SQLite is strongly recommended, but it is an index/cache rather than the canonical archive.

Suggested tables:

```text
messages
media
saved_tags
message_saved_tags
hashtags
message_hashtags
sources
links
```

Useful message fields:

```text
telegram_id
saved_at
original_at
text
source_id
source_title
source_username
source_message_id
source_type
grouped_id
reply_to
edited_at
archive_date
```

Useful media fields:

```text
message_id
relative_path
type
mime_type
original_filename
size
width
height
duration
sha256
```

Enable SQLite FTS5 for message text when convenient.

Important property:

> Deleting `archive.sqlite` must not destroy the archive. It should be rebuildable from JSONL and files.

---

## 14. SMB and NAS Design

SMB/Finder is the primary simple browsing path.

The daily directory structure keeps the number of directory entries bounded and avoids hundreds of thousands of message folders.

Mechanical HDDs are acceptable for canonical media storage because:

- Large media reads are mostly sequential.
- Day-level directories limit directory enumeration.
- Finder/SMB already provides adequate browsing for normal use.

Avoid a single global directory containing every media file.

Avoid unnecessary background scans.

---

## 15. HDD Sleep Requirement

The NAS is configured to spin down mechanical drives when idle.

Therefore the archive design must not require services that periodically wake the disk.

Do **not** require:

- Background filesystem crawlers.
- Photo management daemons.
- Periodic gallery rescans on the NAS.
- Database servers continuously touching the archive.
- Automatic thumbnail generation on the NAS.

Preferred model:

```text
Mac / client machine
    |
    | sync / generate indexes only when explicitly run
    v
NAS archive
    |
    +-- idle when not being used
```

The Telegram API client and synchronization logic should normally run on a Mac/Linux client rather than on the NAS.

---

## 16. Optional Static Gallery

A gallery is optional and should be implemented only if normal SMB/Finder browsing proves insufficient.

If added, prefer a static, rebuildable gallery rather than a permanent application server.

Possible features:

- Images for a selected day.
- Videos for a selected day.
- Source filtering.
- Saved-tag filtering.
- Media-type filtering.
- Chronological order.
- Reverse order.
- Random order.
- Slideshow.
- Video poster thumbnails.

Static HTML + JavaScript is sufficient for random ordering and slideshow behavior.

No backend is required.

Generated gallery files should be considered disposable/rebuildable.

---

## 17. Optional Thumbnails

If a static gallery is introduced, thumbnails may be generated during sync.

Suggested behavior:

- Image: 320-480 px preview.
- Video: one poster frame.
- PDF/other files: no preview in V1.

Do not generate thumbnails lazily by scanning the NAS when the gallery is opened.

If the NAS has SSD storage, gallery indexes/thumbnails may live on SSD while original media remains on HDD. This allows gallery browsing without waking the media disks until the user opens an original.

---

## 18. Incremental Sync

V1 should support incremental synchronization.

The sync state should not rely solely on a single `last_message_id`.

Persist sufficient state to support:

- New messages.
- Added/removed Saved tags.
- Edited messages.
- New media downloads.
- Failed/incomplete media downloads.

Suggested files:

```text
metadata/sync-state.json
logs/
```

Possible modes later:

### Fast sync

- Fetch new messages.
- Refresh relevant Saved tags.
- Download new media.

### Reconcile

Occasionally revisit recent messages to detect metadata/tag/edit changes.

### Audit

Manual integrity check:

- JSONL vs filesystem.
- SQLite vs JSONL.
- Missing media.
- Optional hashes.

Do not make full audits a permanent NAS background job.

---

## 19. Deleted and Edited Messages

The local archive is a historical archive, not merely a mirror.

### Telegram deletion

If a message disappears from Saved Messages after already being archived:

- Do not automatically delete the local copy.
- Mark it as deleted-from-Telegram if detected.

Possible fields:

```text
telegram_status
deleted_detected_at
```

### Message edits

Preserve:

```text
edited_at
```

V1 may update the canonical Markdown/JSONL record.

Historical versioning can be considered later if needed.

---

## 20. Duplicate Detection

Optional V1.5 feature:

Calculate SHA-256 for media and record it in SQLite.

Initially:

- Detect duplicates.
- Do not automatically deduplicate physical files.

Hardlinks/content-addressed storage can be considered later only if archive size becomes problematic.

Reliability and transparent files are more important than aggressive space optimization.

---

## 21. Links

Extract URLs from message text into the index.

Useful fields:

```text
message_id
url
domain
```

This allows future searches such as:

```text
domain:arxiv.org
domain:github.com
domain:youtube.com
```

This can also be valuable to the news/podcast pipeline.

---

## 22. Telegram Session Security

Never place the Telethon session file inside the shared NAS archive.

Example local location:

```text
~/.config/telegram-news-podcast/
├── telegram.session
└── config.toml
```

Use restrictive file permissions.

The NAS archive should contain exported data only, not reusable Telegram authentication state.

---

## 23. Suggested Implementation Phases

### V1 — Core archive

Implement only the essential archive:

- Telethon login/client reuse.
- Iterate Saved Messages.
- Incremental fetch.
- Message text.
- Original media download.
- Daily directory structure.
- Daily Markdown.
- Daily JSONL.
- Saved Messages tags.
- Hashtags.
- Forward source resolution.
- Channel/source names.
- Original message IDs.
- Saved/original timestamps.
- Media-group handling.
- Filename sanitization.
- Download retry/error handling.
- Sync state.
- SQLite basic index.

This is enough for practical SMB/Finder use.

### V1.5 — Search and convenience

Only after V1 proves useful:

- SQLite FTS5.
- URL extraction.
- Media hashes.
- Basic statistics.
- Logical indexes by source/tag/date.
- Optional thumbnails.
- Optional static gallery.

### V2 — Only if actually needed

Possible future enhancements:

- PDF text extraction.
- OCR.
- Video subtitle extraction.
- Web-page metadata.
- AI classification.
- Automatic tags.
- Richer static/browser UI.
- Integration of archived Saved Messages into news/podcast selection.

---

## 24. Final Design Principle

The project should remain an archive first, not a media-management platform.

The canonical data should always be understandable as ordinary files:

```text
Markdown
JSONL
JPEG / PNG / WebP
MP4
PDF
ZIP
other original media
```

Everything else should be disposable:

```text
SQLite index
HTML gallery
thumbnails
search cache
statistics
```

The expected long-term workflow is:

```text
Telegram
   |
   v
Telethon sync on Mac/Linux
   |
   v
Daily human-readable archive
   |
   v
NAS / SMB

Optional:
archive -> rebuildable SQLite/static gallery
archive -> TelegramNewsPodcast/news-processing pipeline
```

This keeps the archive simple, NAS-friendly, HDD-sleep-friendly, and usable even if the surrounding software is abandoned years later.
