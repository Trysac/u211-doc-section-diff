# Testing

The test suite is `tests/test_doc_section_diff.py`. It exercises the public API and the CLI entry point `doc_section_diff.__main__.main`.

- `test_acceptance_parse_sections_ids_and_hash` checks nested duplicate headings: ids `a`, `a/b`, `a/b-2` and the content hash of `a/b`.
- `test_acceptance_diff_rename_and_changes` checks unchanged, modified, added, removed and renamed output for a guide document with a renamed install section, a changed usage section and a new FAQ section.
- `test_acceptance_install_hash_and_normalization` checks the fixed hash `a824981da2d518f9` for `guide/install` and that trailing spaces, CRLF line endings and blank lines around the body do not change it.
- `test_acceptance_rename_threshold` checks a `Setup` -> `Getting started` rename with a changed body at the default threshold and at `rename_threshold=0.96`, where it becomes one removal and one addition.
- `test_acceptance_fenced_code_and_preamble` checks that `#` inside a fenced code block is body text and that text before the first heading becomes `_preamble`.
- `test_acceptance_parent_not_modified_by_child` checks that a parent section stays unchanged when only a child body changes and that empty-body sections are not matched as renames by hash.
- `test_acceptance_limits` checks `input_too_large`, `too_many_sections` and `invalid_threshold` error codes and the 5,000,000-character and 10,000-section boundaries.
- `test_acceptance_cli` runs `main()` with `tmp_path` and `capsys`, checks JSON output with sorted keys, exit codes 1 and 0, and exit code 2 for a missing file.

## Commands

Run the suite with:

```sh
pytest tests/test_doc_section_diff.py
```

## Adding tests

Add plain pytest functions to `tests/test_doc_section_diff.py` and test through `parse_sections`, `diff_sections` or `main`. Use `pytest.raises(DiffError)` for error codes and `tmp_path`/`capsys` for CLI behavior.
