# doc-section-diff

[![PyPI version](https://img.shields.io/pypi/v/trysac-doc-section-diff)](https://pypi.org/project/trysac-doc-section-diff/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-doc-section-diff)](LICENSE)
[![CI](https://github.com/Trysac/u211-doc-section-diff/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u211-doc-section-diff/actions/workflows/ci.yml)

Compare two versions of a Markdown document section by section with stable section ids and content hashes, and report what a RAG index must add, drop, rename or re-embed.

## Problem

When a source document changes, RAG pipelines usually re-chunk and re-embed the whole file, which is slow and costly, or they miss renamed sections and keep stale chunks. What the index needs is not a word diff but a plan: which sections are new, gone, renamed with the same body, or changed and in need of re-embedding. This library parses Markdown headings into sections with stable ids and SHA-256 content hashes and computes exactly that plan.

## Install

```sh
pip install trysac-doc-section-diff
# or
uv add trysac-doc-section-diff
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
from doc_section_diff import diff_sections

old = "# Guide\nIntro text.\n## Install\nRun pip install x.\n"
new = "# Guide\nIntro text.\n## Installation\nRun pip install x.\n## FAQ\nNone yet.\n"

diff = diff_sections(old, new)
print(diff.to_dict())
```

`diff_sections` returns a `SectionDiff` whose `to_dict()` produces JSON-ready lists. In this example `guide/install` is renamed to `guide/installation` with similarity 1.0 and `modified` False, and `guide/faq` is added.

## API

- `parse_sections(markdown, *, max_chars=5_000_000) -> tuple[Section, ...]` splits ATX headings into `Section(id, heading_path, level, body, content_hash)`. Text before the first heading becomes `_preamble` when non-empty.
- `diff_sections(old, new, *, rename_threshold=0.8) -> SectionDiff` returns `unchanged`, `modified`, `added`, `removed` and `renamed` tuples. `SectionDiff.to_dict()` converts them to lists; each `Rename` has `old_id`, `new_id`, `similarity` and `modified`.
- `DiffError` carries `code`: `input_too_large`, `too_many_sections` or `invalid_threshold`.

Limits: each input is limited to 5,000,000 characters and 10,000 sections; `rename_threshold` must be in `(0, 1]`. Only ATX headings are recognized; setext headings are body text, and headings inside fenced code blocks opened by three or more backticks or tildes are ignored.

The CLI prints `SectionDiff.to_dict()` as JSON with sorted keys:

```sh
python -m doc_section_diff old.md new.md
```

It exits `0` when the documents are equivalent, `1` when anything changed, and `2` on usage or I/O errors.

## Why not a text diff

A text diff reports line hunks. This library reports section-level actions (`unchanged`, `modified`, `added`, `removed`, `renamed`) keyed by stable section ids, so a RAG index can decide which sections to add, drop, rename or re-embed without re-chunking the whole document.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Testing](docs/TESTING.md)
- [Security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md)
- [Stack](docs/STACK.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
