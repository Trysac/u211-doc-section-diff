"""Compare two versions of a Markdown document section by section.

Parse ATX headings into sections with stable ids and content hashes, then
diff two markdown documents into a plan that tells a RAG index which
sections to add, drop, rename, or re-embed.
"""

from __future__ import annotations

import difflib
import hashlib
import logging
import re
import unicodedata
from dataclasses import dataclass
from typing import Literal

__all__ = [
    "DiffError",
    "Rename",
    "Section",
    "SectionDiff",
    "__version__",
    "diff_sections",
    "parse_sections",
]

__version__ = "0.1.0"

logger = logging.getLogger(__name__)
if not logger.handlers:
    logger.addHandler(logging.NullHandler())

DiffErrorCode = Literal["input_too_large", "too_many_sections", "invalid_threshold"]


class DiffError(Exception):
    """Error raised for invalid inputs or configuration."""

    def __init__(self, code: DiffErrorCode) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class Section:
    """A single Markdown section with stable identity and content hash."""

    id: str
    heading_path: tuple[str, ...]
    level: int
    body: str
    content_hash: str


@dataclass(frozen=True)
class Rename:
    """A detected rename between two section ids."""

    old_id: str
    new_id: str
    similarity: float
    modified: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "old_id": self.old_id,
            "new_id": self.new_id,
            "similarity": self.similarity,
            "modified": self.modified,
        }


@dataclass(frozen=True)
class SectionDiff:
    """Result of diffing two Markdown documents section by section."""

    unchanged: tuple[str, ...]
    modified: tuple[str, ...]
    added: tuple[str, ...]
    removed: tuple[str, ...]
    renamed: tuple[Rename, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "unchanged": list(self.unchanged),
            "modified": list(self.modified),
            "added": list(self.added),
            "removed": list(self.removed),
            "renamed": [r.to_dict() for r in self.renamed],
        }


def _normalize_newlines(markdown: str) -> str:
    return markdown.replace("\r\n", "\n").replace("\r", "\n")


def _strip_closing_hashes(text: str) -> str:
    text = text.strip()
    i = len(text)
    while i and text[i - 1] == "#":
        i -= 1
    if 0 < i < len(text) and text[i - 1] in " \t":
        head = text[:i].rstrip()
        return head or text
    return text


def _slugify(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    lowered = ascii_text.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered)
    slug = slug.strip("-")
    return slug or "section"


def _parse_heading(line: str) -> tuple[int, str] | None:
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:
        return None
    match = re.match(r"^(#{1,6})[ \t]+(.*)$", stripped)
    if not match:
        return None
    level = len(match.group(1))
    heading_text = _strip_closing_hashes(match.group(2))
    return level, heading_text


def _detect_fence_start(line: str) -> tuple[str, int] | None:
    stripped = line.lstrip(" ")
    if len(line) - len(stripped) > 3:
        return None
    if not stripped:
        return None
    char = stripped[0]
    if char not in ("`", "~"):
        return None
    count = 0
    for ch in stripped:
        if ch == char:
            count += 1
        else:
            break
    if count < 3:
        return None
    return char, count


def _is_fence_close(line: str, char: str, min_count: int) -> bool:
    stripped = line.strip()
    if not stripped.startswith(char):
        return False
    count = 0
    for ch in stripped:
        if ch == char:
            count += 1
        else:
            break
    return count >= min_count and stripped[count:].strip() == ""


def _normalize_body_lines(lines: list[str]) -> str:
    normalized_lines = [line.rstrip() for line in lines]
    start = 0
    end = len(normalized_lines)
    while start < end and normalized_lines[start] == "":
        start += 1
    while end > start and normalized_lines[end - 1] == "":
        end -= 1
    return "\n".join(normalized_lines[start:end])


def _make_section(heading_path: tuple[str, ...], level: int, body_lines: list[str]) -> Section:
    body = _normalize_body_lines(body_lines)
    content_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
    return Section(
        id="/".join(heading_path),
        heading_path=heading_path,
        level=level,
        body=body,
        content_hash=content_hash,
    )


def parse_sections(markdown: str, *, max_chars: int = 5_000_000) -> tuple[Section, ...]:
    """Parse Markdown ATX headings into sections.

    Text before the first heading becomes ``_preamble`` (omitted when empty).
    Setext headings are treated as body text. Fenced code blocks (three or
    more backticks or tildes) suppress heading recognition inside them.

    Args:
        markdown: Input Markdown document (UTF-8 string).
        max_chars: Maximum number of characters allowed in the input.

    Returns:
        Tuple of Section objects in document order.

    Raises:
        DiffError: With codes ``input_too_large`` or ``too_many_sections``.
    """
    if len(markdown) > max_chars:
        raise DiffError("input_too_large")

    normalized = _normalize_newlines(markdown)
    lines = normalized.split("\n")

    sections: list[Section] = []
    pending_preamble: list[str] = []
    current_body: list[str] | None = None
    current_path: tuple[str, ...] | None = None
    current_level = 0
    stack: list[tuple[tuple[str, ...], int]] = []
    used_ids: set[tuple[tuple[str, ...], str]] = set()
    in_fence: tuple[str, int] | None = None
    first_heading_found = False

    for raw_line in lines:
        line = raw_line

        if in_fence is not None:
            fence_char, fence_min = in_fence
            if current_body is not None:
                current_body.append(line)
            else:
                pending_preamble.append(line)
            if _is_fence_close(line, fence_char, fence_min):
                in_fence = None
            continue

        fence_start = _detect_fence_start(line)
        if fence_start is not None:
            in_fence = fence_start
            if current_body is not None:
                current_body.append(line)
            else:
                pending_preamble.append(line)
            continue

        heading_match = _parse_heading(line)
        if heading_match is not None:
            level, heading_text = heading_match

            if current_body is not None:
                sections.append(_make_section(current_path or (), current_level, current_body))

            while stack and stack[-1][1] >= level:
                stack.pop()
            parent_path = stack[-1][0] if stack else ()
            slug = _slugify(heading_text)
            unique_slug = slug
            n = 1
            while (parent_path, unique_slug) in used_ids:
                n += 1
                unique_slug = f"{slug}-{n}"
            used_ids.add((parent_path, unique_slug))
            new_path = (*parent_path, unique_slug)

            current_path = new_path
            current_level = level
            current_body = []
            stack.append((new_path, level))
            first_heading_found = True
            continue

        if current_body is not None:
            current_body.append(line)
        else:
            pending_preamble.append(line)

    if current_body is not None:
        sections.append(_make_section(current_path or (), current_level, current_body))

    if first_heading_found:
        preamble_body = _normalize_body_lines(pending_preamble)
        if preamble_body:
            preamble_path = ("_preamble",)
            preamble = Section(
                id="_preamble",
                heading_path=preamble_path,
                level=0,
                body=preamble_body,
                content_hash=hashlib.sha256(preamble_body.encode("utf-8")).hexdigest()[:16],
            )
            sections.insert(0, preamble)
    else:
        preamble_body = _normalize_body_lines(pending_preamble)
        if preamble_body:
            sections.append(
                Section(
                    id="_preamble",
                    heading_path=("_preamble",),
                    level=0,
                    body=preamble_body,
                    content_hash=hashlib.sha256(preamble_body.encode("utf-8")).hexdigest()[:16],
                )
            )

    if len(sections) > 10_000:
        raise DiffError("too_many_sections")

    return tuple(sections)


def diff_sections(
    old: str,
    new: str,
    *,
    rename_threshold: float = 0.8,
) -> SectionDiff:
    """Diff two Markdown documents section by section.

    Args:
        old: Old document text.
        new: New document text.
        rename_threshold: Minimum SequenceMatcher ratio to consider a rename.

    Returns:
        SectionDiff with ids in new-document order for added, old-document order
        for removed.

    Raises:
        DiffError: With code ``invalid_threshold`` if threshold is outside (0, 1].
    """
    if not (0 < rename_threshold <= 1):
        raise DiffError("invalid_threshold")

    old_sections = parse_sections(old)
    new_sections = parse_sections(new)

    old_by_id = {s.id: s for s in old_sections}

    unchanged: list[str] = []
    modified: list[str] = []
    matched_old_ids: set[str] = set()
    matched_new_ids: set[str] = set()

    for new_s in new_sections:
        if new_s.id in old_by_id:
            old_s = old_by_id[new_s.id]
            if old_s.content_hash == new_s.content_hash:
                unchanged.append(new_s.id)
            else:
                modified.append(new_s.id)
            matched_old_ids.add(new_s.id)
            matched_new_ids.add(new_s.id)

    remaining_old = [s for s in old_sections if s.id not in matched_old_ids]
    remaining_new = [s for s in new_sections if s.id not in matched_new_ids]

    renames: list[Rename] = []

    for old_s in list(remaining_old):
        if old_s.body == "":
            continue
        for new_s in list(remaining_new):
            if new_s.body == "":
                continue
            if old_s.content_hash == new_s.content_hash:
                renames.append(Rename(old_s.id, new_s.id, 1.0, False))
                remaining_old.remove(old_s)
                remaining_new.remove(new_s)
                break

    old_index = {s.id: i for i, s in enumerate(old_sections)}
    new_index = {s.id: i for i, s in enumerate(new_sections)}
    pairs: list[tuple[float, str, str, Section, Section]] = []

    for old_s in remaining_old:
        if old_s.body == "":
            continue
        for new_s in remaining_new:
            if new_s.body == "":
                continue
            ratio = difflib.SequenceMatcher(None, old_s.body, new_s.body).ratio()
            if ratio >= rename_threshold:
                pairs.append((ratio, old_s.id, new_s.id, old_s, new_s))

    pairs.sort(key=lambda x: (-x[0], old_index[x[1]], new_index[x[2]]))

    used_old: set[str] = set()
    used_new: set[str] = set()

    for ratio, old_id, new_id, old_s, new_s in pairs:
        if old_id in used_old or new_id in used_new:
            continue
        used_old.add(old_id)
        used_new.add(new_id)
        similarity = round(ratio, 3)
        modified_flag = old_s.content_hash != new_s.content_hash
        renames.append(Rename(old_id, new_id, similarity, modified_flag))

    removed = [s.id for s in remaining_old if s.id not in used_old]
    added = [s.id for s in remaining_new if s.id not in used_new]

    return SectionDiff(
        unchanged=tuple(unchanged),
        modified=tuple(modified),
        added=tuple(added),
        removed=tuple(removed),
        renamed=tuple(renames),
    )
