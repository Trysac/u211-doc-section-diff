# 0001 - Stdlib only, with difflib for rename similarity

## Context

The library must compare Markdown section bodies to decide whether a section was renamed. Candidate
approaches are a third-party diff library, a hand-written similarity metric, or `difflib` from the
standard library. The package is published as a small open-source utility and should install and
audit cheaply.

## Decision

Use only the Python standard library: `hashlib` for content hashes, `unicodedata` and `re` for
slugs, and `difflib.SequenceMatcher(None, old_body, new_body).ratio()` for rename similarity.
Runtime dependencies stay empty.

## Consequences

- No supply-chain surface and no installation friction.
- Similarity is the well-known `SequenceMatcher` ratio; it is good enough for section-level
  renames and is documented as such.
- Word-level diffs and more advanced similarity metrics remain out of scope.
