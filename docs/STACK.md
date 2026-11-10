# Stack

| Concern | Choice | Reason |
|---|---|---|
| Language | Python >= 3.10 | Uses modern typing syntax such as `tuple[str, ...]` and `list[str] | None`, frozen dataclasses and type hints. |
| Runtime dependencies | none | Only the standard library is imported: `hashlib`, `difflib`, `unicodedata`, `re`, `json`, `pathlib`, `dataclasses`, `logging` and `typing`. |
| Packaging | `py.typed` included | The package ships a `py.typed` marker. |
| Tests | pytest | `tests/test_doc_section_diff.py` contains pytest functions and uses `pytest.raises`, `tmp_path` and `capsys`. |

## Discarded

- Third-party diff libraries: `difflib.SequenceMatcher` provides the similarity ratio used for rename detection, so the package stays dependency-free.
- Setext heading parsing: setext headings are treated as body text; parsing them is out of scope.
