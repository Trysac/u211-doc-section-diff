"""Tests for doc_section_diff package."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from doc_section_diff import DiffError, Rename, diff_sections, parse_sections
from doc_section_diff.__main__ import main


def test_acceptance_parse_sections_ids_and_hash() -> None:
    markdown = (
        "# A"
        + chr(10)
        + "x"
        + chr(10)
        + "## B"
        + chr(10)
        + "y"
        + chr(10)
        + "## B"
        + chr(10)
        + "z"
        + chr(10)
    )
    sections = parse_sections(markdown)
    assert [s.id for s in sections] == ["a", "a/b", "a/b-2"]
    assert sections[1].content_hash == hashlib.sha256(b"y").hexdigest()[:16]


def test_acceptance_diff_rename_and_changes() -> None:
    old = (
        "# Guide"
        + chr(10)
        + "Intro text."
        + chr(10)
        + "## Install"
        + chr(10)
        + "Run pip install x."
        + chr(10)
        + "## Usage"
        + chr(10)
        + "Call x()."
        + chr(10)
    )
    new = (
        "# Guide"
        + chr(10)
        + "Intro text."
        + chr(10)
        + "## Installation"
        + chr(10)
        + "Run pip install x."
        + chr(10)
        + "## Usage"
        + chr(10)
        + "Call x(1)."
        + chr(10)
        + "## FAQ"
        + chr(10)
        + "None yet."
        + chr(10)
    )
    diff = diff_sections(old, new)
    assert diff.unchanged == ("guide",)
    assert diff.modified == ("guide/usage",)
    assert diff.added == ("guide/faq",)
    assert diff.removed == ()
    assert diff.renamed == (Rename("guide/install", "guide/installation", 1.0, False),)


def test_acceptance_install_hash_and_normalization() -> None:
    expected_hash = "a824981da2d518f9"
    body = "Run pip install x."
    assert hashlib.sha256(body.encode("utf-8")).hexdigest()[:16] == expected_hash

    base = "# Guide" + chr(10) + "## Install" + chr(10) + "Run pip install x." + chr(10)
    trailing = "# Guide" + chr(10) + "## Install" + chr(10) + "Run pip install x.  " + chr(10)
    crlf = (
        "# Guide"
        + chr(13)
        + chr(10)
        + "## Install"
        + chr(13)
        + chr(10)
        + "Run pip install x."
        + chr(13)
        + chr(10)
    )
    blank = (
        "# Guide"
        + chr(10)
        + "## Install"
        + chr(10)
        + chr(10)
        + "Run pip install x."
        + chr(10)
        + chr(10)
    )

    for md in (base, trailing, crlf, blank):
        sections = parse_sections(md)
        install = next(s for s in sections if s.id == "guide/install")
        assert install.content_hash == expected_hash


def test_acceptance_rename_threshold() -> None:
    old = "## Setup" + chr(10) + "Install the package with pip and run init." + chr(10)
    new = (
        "## Getting started" + chr(10) + "Install the package with pip and run init now." + chr(10)
    )
    diff = diff_sections(old, new)
    assert diff.renamed == (Rename("setup", "getting-started", 0.955, True),)
    assert diff.modified == ()
    assert diff.removed == ()
    assert diff.added == ()

    diff_high = diff_sections(old, new, rename_threshold=0.96)
    assert diff_high.renamed == ()
    assert diff_high.removed == ("setup",)
    assert diff_high.added == ("getting-started",)


def test_acceptance_fenced_code_and_preamble() -> None:
    md = "# A" + chr(10) + "```" + chr(10) + "# not a heading" + chr(10) + "```" + chr(10)
    sections = parse_sections(md)
    assert [s.id for s in sections] == ["a"]
    assert sections[0].body == "```" + chr(10) + "# not a heading" + chr(10) + "```"

    preamble_md = "Intro" + chr(10) + "# A" + chr(10) + "Body" + chr(10)
    sections2 = parse_sections(preamble_md)
    assert [s.id for s in sections2] == ["_preamble", "a"]
    assert sections2[0].body == "Intro"


def test_acceptance_parent_not_modified_by_child() -> None:
    old = "# A" + chr(10) + "x" + chr(10) + "## B" + chr(10) + "y" + chr(10)
    new = "# A" + chr(10) + "x" + chr(10) + "## B" + chr(10) + "z" + chr(10)
    diff = diff_sections(old, new)
    assert diff.unchanged == ("a",)
    assert diff.modified == ("a/b",)


def test_acceptance_limits() -> None:
    with pytest.raises(DiffError) as exc_info:
        parse_sections("x" * 5_000_001)
    assert exc_info.value.code == "input_too_large"

    parse_sections("x" * 5_000_000)

    too_many = "" + chr(10).join(["# h"] * 10_001) + chr(10)
    with pytest.raises(DiffError) as exc_info2:
        parse_sections(too_many)
    assert exc_info2.value.code == "too_many_sections"

    with pytest.raises(DiffError) as exc_info3:
        diff_sections("# A" + chr(10), "# A" + chr(10), rename_threshold=0)
    assert exc_info3.value.code == "invalid_threshold"

    with pytest.raises(DiffError) as exc_info4:
        diff_sections("# A" + chr(10), "# A" + chr(10), rename_threshold=1.5)
    assert exc_info4.value.code == "invalid_threshold"


def test_acceptance_cli(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    old_file = tmp_path / "old.md"
    new_file = tmp_path / "new.md"
    old_file.write_text("# A" + chr(10) + "x" + chr(10), encoding="utf-8")
    new_file.write_text("# A" + chr(10) + "y" + chr(10), encoding="utf-8")

    rc = main([str(old_file), str(new_file)])
    captured = capsys.readouterr()
    assert rc == 1
    data = json.loads(captured.out)
    assert data["modified"] == ["a"]
    assert "added" in data and "removed" in data and "renamed" in data and "unchanged" in data

    old_file.write_text("# A" + chr(10) + "x" + chr(10), encoding="utf-8")
    new_file.write_text("# A" + chr(10) + "x" + chr(10), encoding="utf-8")
    rc = main([str(old_file), str(new_file)])
    captured = capsys.readouterr()
    assert rc == 0

    missing = tmp_path / "missing.md"
    rc = main([str(old_file), str(missing)])
    captured = capsys.readouterr()
    assert rc == 2


def test_section_moved_under_new_parent_is_rename() -> None:
    old = "# A" + chr(10) + "## B" + chr(10) + "body" + chr(10)
    new = "# C" + chr(10) + "## B" + chr(10) + "body" + chr(10)
    diff = diff_sections(old, new)
    assert diff.renamed == (Rename("a/b", "c/b", 1.0, False),)


def test_slug_punctuation_and_accents() -> None:
    md = "# Caf\u00e9 & Co" + chr(10) + "x" + chr(10)
    sections = parse_sections(md)
    assert sections[0].id == "cafe-co"


def test_identical_documents() -> None:
    md = "# A" + chr(10) + "x" + chr(10)
    diff = diff_sections(md, md)
    assert diff.unchanged == ("a",)
    assert diff.modified == ()
    assert diff.added == ()
    assert diff.removed == ()
    assert diff.renamed == ()


def test_empty_document() -> None:
    assert parse_sections("") == ()


def test_setext_headings_are_body_text() -> None:
    md = "# A" + chr(10) + "Title" + chr(10) + "=====" + chr(10)
    sections = parse_sections(md)
    assert sections[0].body == "Title" + chr(10) + "====="


def test_section_diff_to_dict() -> None:
    old = "# A" + chr(10) + "x" + chr(10) + "## B" + chr(10) + "y" + chr(10)
    new = "# A" + chr(10) + "x" + chr(10) + "## C" + chr(10) + "y" + chr(10)
    diff = diff_sections(old, new)
    data = diff.to_dict()
    assert data["unchanged"] == ["a"]
    assert data["renamed"] == [
        {"old_id": "a/b", "new_id": "a/c", "similarity": 1.0, "modified": False}
    ]


def test_duplicate_sections_keep_distinct_ids() -> None:
    md = "# A" + chr(10) + "## B" + chr(10) + "## B" + chr(10) + "## B-2" + chr(10)
    sections = parse_sections(md)
    assert [s.id for s in sections] == ["a", "a/b", "a/b-2", "a/b-2-2"]


def test_empty_body_sections_are_never_hash_renames() -> None:
    diff = diff_sections(
        "# A" + chr(10) + "## B" + chr(10) + "body" + chr(10),
        "# C" + chr(10) + "## B" + chr(10) + "body" + chr(10),
    )
    assert diff.renamed == (Rename("a/b", "c/b", 1.0, False),)
    assert diff.removed == ("a",)
    assert diff.added == ("c",)

    diff_empty = diff_sections("# A" + chr(10) + "# B" + chr(10), "# C" + chr(10) + "# D" + chr(10))
    assert diff_empty.renamed == ()
    assert diff_empty.removed == ("a", "b")
    assert diff_empty.added == ("c", "d")


def test_closing_hashes_scan_is_linear_on_long_whitespace() -> None:
    start = time.monotonic()
    sections = parse_sections("# a" + " " * 200_000 + "#x" + chr(10))
    assert time.monotonic() - start < 5.0
    assert sections[0].id == "a-x"


def test_readme_python_examples_run() -> None:
    readme = Path(__file__).resolve().parent.parent / "README.md"
    text = readme.read_text(encoding="utf-8")
    blocks = re.findall(r"```python\n(.*?)```", text, re.DOTALL)
    assert blocks
    env = dict(os.environ)
    src = str(readme.parent / "src")
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    for block in blocks:
        result = subprocess.run(
            [sys.executable, "-c", block],
            capture_output=True,
            text=True,
            check=False,
            cwd=readme.parent,
            env=env,
        )
        assert result.returncode == 0, result.stderr
