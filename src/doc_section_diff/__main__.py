"""Command-line entry point for doc_section_diff."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from . import DiffError, diff_sections


def main(argv: list[str] | None = None) -> int:
    """Run the section diff CLI.

    Args:
        argv: Command line arguments. Defaults to ``sys.argv[1:]``.

    Returns:
        0 when the two documents are equivalent, 1 when anything changed,
        2 on usage errors or I/O errors.
    """
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print("usage: python -m doc_section_diff OLD.md NEW.md", file=sys.stderr)
        return 2

    old_path = Path(args[0])
    new_path = Path(args[1])
    try:
        old_text = old_path.read_text(encoding="utf-8")
        new_text = new_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error reading files: {exc}", file=sys.stderr)
        return 2

    try:
        section_diff = diff_sections(old_text, new_text)
    except DiffError as exc:
        print(f"error computing diff: {exc.code}", file=sys.stderr)
        return 2

    data = section_diff.to_dict()
    json.dump(data, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")

    return 1 if (data["modified"] or data["added"] or data["removed"] or data["renamed"]) else 0


if __name__ == "__main__":
    raise SystemExit(main())
