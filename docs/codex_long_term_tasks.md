# Codex Long-Term Tasks — Telegram Archive Roadmap

This file contains deferred tasks.

Do not implement these simply because they are possible. Pull them into active work only after V1 is stable and there is a demonstrated need.

---

## LT-01 — Logical browse indexes by source/tag/date

Status: [ ]

Purpose:
Generate lightweight human-readable indexes without duplicating media.

Possible outputs:

```text
browse/
├── by-source/
├── by-tag/
├── by-date/
└── untagged/
```

Preferred format:
- monthly Markdown index files;
- links back to canonical archive paths.

Prerequisites:
- ST-20 complete.
- Real-world SMB usage shows that direct date browsing is insufficient.

Do not:
- copy the same media into multiple index trees;
- rely on symlinks unless NAS/SMB behavior has been explicitly tested.

---

## LT-02 — Static HTML gallery

Status: [ ]

Purpose:
Provide optional image/video browsing without running a permanent NAS service.

Potential features:
- day view;
- image-only view;
- video-only view;
- source filter;
- tag filter;
- chronological/reverse/random ordering;
- slideshow;
- video poster frame.

Architecture requirement:
- static HTML/CSS/JS only where practical;
- generated on Mac/Linux during explicit sync/build;
- no always-on backend required;
- gallery must be disposable and rebuildable.

Prerequisites:
- V1 archive stable.
- User confirms Finder/SMB alone is insufficient.

---

## LT-03 — Thumbnail/poster generation

Status: [ ]

Purpose:
Improve gallery performance on mechanical HDDs.

Possible behavior:
- image previews: 320-480 px;
- video: one poster frame;
- no PDF preview initially.

Requirements:
- generate during explicit sync/build, not through background NAS scanning;
- originals never modified;
- thumbnails are disposable cache.

Optional optimization:
If NAS has SSD storage, allow gallery/index/thumbnails to reside on SSD while originals stay on HDD.

Prerequisites:
- LT-02 approved.

---

## LT-04 — Media metadata enrichment

Status: [ ]

Possible fields:
- image width/height;
- EXIF basics;
- video duration/resolution/codec/fps;
- audio duration;
- document MIME/size.

Principle:
Extract once during ingest or explicit rebuild; do not repeatedly probe all files during normal browsing.

Prerequisites:
- Need demonstrated by gallery/search usage.

---

## LT-05 — Duplicate detection and optional deduplication

Status: [ ]

Phase A:
- compute SHA-256;
- report duplicate groups;
- do not alter physical storage.

Phase B, only if necessary:
- evaluate hardlinks or content-addressed storage.

Constraints:
- human-readable archive paths remain primary;
- SMB/NAS filesystem compatibility must be verified first;
- no deduplication that makes archive recovery obscure.

---

## LT-06 — Rich source-aware search

Status: [ ]

Potential query dimensions:
- source
- date range
- Saved tag
- hashtag
- media type
- text keyword
- domain/link host
- tagged/untagged

Possible implementation:
- SQLite query helpers;
- CLI commands;
- static export of search results.

Avoid introducing a server solely for this feature unless clearly justified.

---

## LT-07 — Link extraction and domain indexing

Status: [ ]

Purpose:
Make Saved Messages containing external resources easier to find and reusable by the podcast/news workflow.

Store:
- URL
- domain
- normalized URL where safe

Potential searches:
- `domain:arxiv.org`
- `domain:github.com`
- `domain:youtube.com`

Potential podcast use:
feed selected saved links into later summarization/content-selection stages.

---

## LT-08 — Integration with TelegramNewsPodcast normalized ingestion

Status: [ ]

Purpose:
Allow the podcast/news pipeline to consume either:
- live channel messages;
- archived Saved Messages;
- both through a common normalized record interface.

Tasks:
- define shared normalized message schema;
- adapt existing `getdata.py` workflow;
- avoid duplicated source/date/text normalization;
- preserve the ability to run the existing workflow independently.

Prerequisites:
- archive record schema stable.
- existing podcast pipeline requirements documented.

---

## LT-09 — Configurable source/tag selection for podcast generation

Status: [ ]

Purpose:
Use archive metadata as an input selector.

Examples:
- only Saved Messages tagged `News`;
- only selected channels;
- date-bounded selections;
- exclude specific tags/sources.

Important:
This is downstream selection logic. It must not alter canonical archive data.

---

## LT-10 — Static statistics

Status: [ ]

Potential outputs:
- messages per month;
- media counts;
- storage size by media type;
- source counts;
- tag counts;
- untagged count.

Requirements:
- generated explicitly, not by a permanent service;
- derived entirely from archive/SQLite;
- no background NAS scans.

---

## LT-11 — Full audit / integrity command

Status: [ ]

Possible checks:
- JSONL records vs files;
- missing media;
- duplicate paths;
- orphan media;
- SQLite vs JSONL;
- optional hash verification;
- schema-version consistency.

Requirements:
- manual command;
- never scheduled by default on a NAS with HDD sleep.

Suggested output:
- summary first;
- machine-readable detailed report optionally written to logs.

---

## LT-12 — Migration/schema tooling

Status: [ ]

Purpose:
Allow archive metadata schema to evolve without re-downloading Telegram history.

Requirements:
- every JSONL record carries schema version;
- migrations operate on local canonical metadata;
- migrations are restartable;
- backup/rollback guidance documented.

Implement only when the first incompatible schema change is actually needed.

---

## LT-13 — Deleted/edit history preservation

Status: [ ]

V1 only needs current canonical content plus deletion/edit status.

Possible future history mode:
- retain previous text/tag versions;
- record when a change was detected;
- keep compact history metadata.

Avoid creating one file per edit unless there is a demonstrated need.

---

## LT-14 — PDF/document text extraction

Status: [ ]

Purpose:
Improve search over archived documents.

Constraints:
- extracted text is derived cache;
- original documents remain unchanged;
- no OCR by default;
- no background full-library rescans.

Implement selectively by MIME type.

---

## LT-15 — OCR

Status: [ ]

Purpose:
Search text contained in images/screenshots.

This is intentionally deferred because it increases compute cost, index size, and project scope.

Prerequisites:
- archive and basic search are stable;
- user confirms OCR provides real value.

Derived OCR text must never replace original media.

---

## LT-16 — Video/audio transcript indexing

Status: [ ]

Purpose:
Search spoken content.

Constraints:
- optional;
- generated explicitly;
- transcripts are derived data;
- no continuous NAS workers.

Implement only for selected media or on demand.

---

## LT-17 — AI classification / automatic tags

Status: [ ]

Purpose:
Suggest categories for untagged archive items.

Strict principle:
- Telegram Saved tags and original hashtags remain ground truth;
- AI tags must be clearly separated as derived suggestions;
- automatic classification must not rewrite original Telegram metadata;
- no always-running inference service required.

Possible fields:
- `derived_tags`
- `classification_model`
- `classified_at`

This should remain late-stage work.

---

## LT-18 — Optional richer local application

Status: [ ]

Only consider a real local web application if static indexes/gallery prove insufficient.

Possible triggers:
- complex compound searches are used frequently;
- random browsing becomes a primary use case;
- static rebuild times become inconvenient.

If implemented:
- keep backend lightweight;
- allow manual start/stop;
- do not require permanent NAS residency;
- continue treating Markdown/JSONL/media as canonical.

Do not introduce a database server when SQLite is sufficient.

---

## LT-19 — NAS deployment mode

Status: [ ]

Optional future mode for users who want the sync process itself on the NAS.

Prerequisites:
- explicit acceptance that scheduled sync may wake HDDs;
- NAS has a suitable place for session/config secrets;
- clear separation between application state and archive data.

Default architecture should remain client-driven sync from Mac/Linux.

---

## LT-20 — Retention/export tooling

Status: [ ]

Possible features:
- export a date range;
- export one source;
- export one tag;
- copy selected media plus Markdown metadata;
- produce portable bundles.

Constraint:
Exports may be compressed for transport if requested, but the canonical archive itself must remain ordinary files.

---

# Long-term promotion rules

A long-term item should be moved into the short-term backlog only when:

1. its prerequisite tasks are complete;
2. there is a concrete user need;
3. the implementation does not compromise human-readable canonical storage;
4. it does not create unnecessary NAS background activity;
5. it can be tested and reported independently.

When promoting a task, copy it into the short-term file with:
- a new short-term ID;
- clear acceptance criteria;
- validation steps;
- explicit dependencies.

Do not work directly from this roadmap without promotion unless the task is purely documentation.
