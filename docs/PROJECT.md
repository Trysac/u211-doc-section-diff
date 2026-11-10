# Project record

## Problem

When a source document changes, RAG pipelines usually re-chunk and re-embed the whole file, which is slow and costly, or they miss renamed sections and keep stale chunks. A text diff is not the right output: the index needs a section-level plan of what to add, drop, rename or re-embed.

## Solution

`doc-section-diff` parses Markdown ATX headings into sections with stable ids and content hashes and diffs two versions into unchanged, modified, added, removed and renamed entries. Rename detection uses equal hashes first and a `difflib.SequenceMatcher` similarity ratio for the rest.

## Scope

In scope:

- Markdown ATX headings as section boundaries.
- Fenced code blocks opened by three or more backticks or tildes suppressing heading recognition.
- Stable section ids and SHA-256 content hashes.
- Section-level diff actions: unchanged, modified, added, removed, renamed.
- A JSON CLI (`python -m doc_section_diff OLD.md NEW.md`).

Out of scope:

- Word-level or line-level diffs for human review.
- Setext headings; they are treated as body text.
- Other document formats; convert them to Markdown first.

## Status

Version 0.1.0, public open source, standard library only, Python 3.10 or newer.

## Factory run u211 (measured from API usage)

| Date (UTC) | Phase | Model | Batch | Input | Output | Cache write | Cache read | Cost (USD) |
|---|---|---|---|---|---|---|---|---|
| 2026-11-10 | generation | deepseek-v4-pro | yes | 1882 | 22063 | 0 | 3200 | 0.0450 |
| 2026-11-10 | fix-1 | deepseek-flash | no | 9787 | 1539 | 0 | 42624 | 0.0025 |
| 2026-11-10 | audit | deepseek-flash | no | 14769 | 18709 | 0 | 226688 | 0.0141 |
| 2026-11-10 | fix-2 | deepseek-flash | no | 17962 | 12446 | 0 | 290304 | 0.0110 |
| 2026-11-10 | docs | deepseek-flash | no | 110127 | 12450 | 0 | 256 | 0.0240 |

Total: $0.0967. Prices: deepseek line, as measured by its adapter. Providers serve the current version of each model id, so the date tells which version answered; versions, launch stages and price sources per line are in the factory's model register (docs/MODELS.md).
