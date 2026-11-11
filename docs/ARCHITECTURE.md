# Architecture

`doc_section_diff` is a single standard-library module, `src/doc_section_diff/__init__.py`, plus a thin CLI in `src/doc_section_diff/__main__.py`. There are no runtime dependencies.

## Public API

- `parse_sections(markdown: str, *, max_chars: int = 5_000_000) -> tuple[Section, ...]`
- `diff_sections(old: str, new: str, *, rename_threshold: float = 0.8) -> SectionDiff`
- `Section(id, heading_path, level, body, content_hash)`
- `SectionDiff(unchanged, modified, added, removed, renamed)` with `to_dict()`
- `Rename(old_id, new_id, similarity, modified)`
- `DiffError(code)` with codes `input_too_large`, `too_many_sections`, `invalid_threshold`

## Parsing

Only ATX headings (one to six `#` followed by a space or tab) start a section. Indentation of more than three spaces prevents a heading from being recognized. Headings inside fenced code blocks opened by three or more backticks or tildes are body text, as are setext headings. Text before the first heading becomes `_preamble` when non-empty; if the document has no heading, non-empty text is also returned as `_preamble`.

A section body runs from its heading to the next heading of any level, so child sections are separate entries and a parent body does not include child text. Bodies are normalized: CRLF and CR become LF, each line is right-stripped, and leading and trailing blank lines are removed. `content_hash` is the first 16 hex characters of the SHA-256 of the normalized body encoded as UTF-8.

Ids are the heading path slugs joined by `/`. Slugs lowercase, NFKD-normalize and drop combining marks, replace runs of non `[a-z0-9]` characters with `-`, strip `-`, and fall back to `section` when empty. Repeated ids among siblings receive `-2`, `-3` in order; ids actually handed out are tracked so a heading that itself ends in such a suffix still gets a distinct id.

## Diff algorithm

1. Ids present in both versions are unchanged when their hashes match, otherwise modified.
2. Unmatched sections with non-empty bodies and equal hashes are renames with similarity `1.0` and `modified` False. Each section is used once, scanning old sections in old-document order and new sections in new-document order.
3. Remaining pairs with non-empty bodies are scored with `difflib.SequenceMatcher(None, old_body, new_body).ratio()`. Pairs at or above `rename_threshold` are matched greedily by highest ratio; ties follow old-document order then new-document order. Similarity is rounded to three decimals and `modified` is True when the content hashes differ.
4. The rest are added or removed.

Empty-body sections are never matched by hash or similarity. Output order follows the new document for `unchanged`, `modified` and `added`, and the old document for `removed`.

## CLI

`python -m doc_section_diff OLD.md NEW.md` prints `SectionDiff.to_dict()` as JSON with sorted keys and returns 0 when nothing changed, 1 when anything changed, and 2 on usage or I/O errors.
