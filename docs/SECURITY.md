# Security

The reporting process for vulnerabilities is in the [root security policy](../SECURITY.md). Do not open a public issue for a vulnerability.

## Threat model

`parse_sections` and `diff_sections` process untrusted Markdown. The library does not execute, evaluate, fetch, render or sanitize the input; it only normalizes text, splits ATX headings and hashes section bodies. It has no runtime dependencies.

Defended:

- Oversized input: `parse_sections` rejects more than `max_chars` characters (default 5,000,000) with `DiffError("input_too_large")`.
- Excessive section count: more than 10,000 sections raises `DiffError("too_many_sections")`.
- Invalid rename configuration: `diff_sections` rejects `rename_threshold` outside `(0, 1]` with `DiffError("invalid_threshold")`.
- Catastrophic backtracking in heading cleanup: `_strip_closing_hashes` is a linear scan, and `_parse_heading` uses a simple anchored pattern.
- Rename cost: similarity scoring runs only on sections that remain unmatched after id and hash matching.

Not defended:

- Markdown rendering, HTML sanitization or execution of code blocks is not performed.
- Downstream consumers must still treat section text and headings as untrusted data.
- The CLI reads files named on the command line; file access control is the caller's responsibility.

## Mitigations

- `max_chars` (default 5,000,000) rejects oversized input with `DiffError("input_too_large")`.
- At most 10,000 sections are allowed; more raises `DiffError("too_many_sections")`.
- Heading cleanup uses a linear scan instead of a backtracking regular expression, so long runs of whitespace in a heading cannot cause catastrophic backtracking.
- Rename scoring only runs on section bodies that remain unmatched, and `rename_threshold` is validated to be in `(0, 1]`.

No secrets, tokens or credentials are read or logged. Logging uses `logging.getLogger(__name__)` with a `NullHandler`.
