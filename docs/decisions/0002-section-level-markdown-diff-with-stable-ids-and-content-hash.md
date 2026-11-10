# Section-level Markdown diff with stable ids and content hashes

Status: accepted (generated, pending human review)

## Context

When a source document changes, RAG pipelines often re-chunk and re-embed the whole file, which is slow and costly, or they miss renamed sections and keep stale chunks. The index needs a plan: which sections are new, gone, renamed with the same body, or changed and in need of re-embedding.

## Decision

Implement a stdlib-only Python package that parses ATX Markdown headings into sections with stable slug-based ids and SHA-256 content hashes, then computes a diff using id matching, hash-based renames, and difflib.SequenceMatcher similarity for renamed or modified bodies. Output IDs follow document/new order where applicable.

## Consequences

The API returns actionable section-level changes instead of line hunks. Stable ids make renames detectable; content hashes avoid false renames by body equality. Limits on input size, section count, and rename threshold protect against pathological inputs. The CLI outputs JSON for easy integration into indexing pipelines.
