# doc-section-diff

[![PyPI version](https://img.shields.io/pypi/v/trysac-doc-section-diff)](https://pypi.org/project/trysac-doc-section-diff/)
[![License: MIT](https://img.shields.io/pypi/l/trysac-doc-section-diff)](LICENSE)
[![CI](https://github.com/Trysac/u211-doc-section-diff/actions/workflows/ci.yml/badge.svg)](https://github.com/Trysac/u211-doc-section-diff/actions/workflows/ci.yml)

Compare two versions of a Markdown document section by section with stable section ids and content hashes, and report what a RAG index must add, drop, rename or re-embed

## Problem

Describe in two or three sentences the concrete problem this utility solves, who hits it, and what
they do today without it. Replace this paragraph when the first real feature lands.

## Install

```sh
pip install trysac-doc-section-diff
# or
uv add trysac-doc-section-diff
```

Requires Python 3.10 or newer. No runtime dependencies.

## Usage

```python
import doc_section_diff

# normalize() trims surrounding whitespace and lower-cases the text.
print(doc_section_diff.normalize("  Hello World "))  # -> "hello world"

# Blank input is rejected explicitly instead of returning an empty string.
try:
    doc_section_diff.normalize("   ")
except ValueError as exc:
    print(f"rejected: {exc}")
```

## Documentation

- [Architecture](docs/ARCHITECTURE.md) and [decisions](docs/decisions/)
- [Testing](docs/TESTING.md) and [security](docs/SECURITY.md)
- [Project record](docs/PROJECT.md) and [stack](docs/STACK.md)
- [Changelog](CHANGELOG.md) and [contributing guide](CONTRIBUTING.md)

## License

[MIT](LICENSE) (c) 2026 Miguel Gomez
