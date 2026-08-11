"""Heading-aware chunking of the knowledge base (Day-7/8 pipeline).

Markdown structure is the natural chunk boundary here: every `##` in `knowledge/raw` is
already a self-contained answer unit written for a human. Chunking on headings means a
chunk never straddles two topics, which is what makes a citation meaningful — a cited
chunk is a section a recruiter can open and verify.

Two rules earn their complexity:

* **Tables are never split.** A markdown table cut in half produces a chunk of orphan
  rows with no header, which retrieves well and reads as nonsense.
* **Oversized sections keep their heading.** When a section must be split, every part
  carries the same heading, so a fragment retrieved on its own still says what it is.
"""

from __future__ import annotations

import re
from pathlib import Path

from agent.schemas import Chunk

TARGET_TOKENS = 450
OVERLAP_TOKENS = 60
MIN_TOKENS = 25

_FRONT_MATTER = re.compile(r"^---\n(.*?)\n---\n", re.S)
_H2 = re.compile(r"^## +(.+?)\s*$", re.M)


def estimate_tokens(text: str) -> int:
    """Word count times 1.3. Close enough to size a chunk; never used for billing."""
    return int(len(text.split()) * 1.3)


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def parse_front_matter(raw: str) -> tuple[dict, str]:
    """Return `(metadata, body)`. Missing front matter is a build error, not a default."""
    match = _FRONT_MATTER.match(raw)
    if not match:
        return {}, raw
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t", "-")):
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, raw[match.end():]


def split_sections(body: str) -> list[tuple[str, str]]:
    """Split on `##`, keeping any preamble under the document's own `#` title."""
    matches = list(_H2.finditer(body))
    if not matches:
        title = re.search(r"^# +(.+?)\s*$", body, re.M)
        return [((title.group(1) if title else "Overview"), body.strip())]

    sections: list[tuple[str, str]] = []
    preamble = body[: matches[0].start()].strip()
    if preamble:
        title = re.search(r"^# +(.+?)\s*$", preamble, re.M)
        text = _H2.sub("", preamble).strip()
        text = re.sub(r"^# +.+?\s*$", "", text, flags=re.M).strip()
        if estimate_tokens(text) >= MIN_TOKENS:
            sections.append(((title.group(1) if title else "Overview"), text))

    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
        sections.append((match.group(1).strip(), body[match.end():end].strip()))
    return sections


def _blocks(text: str) -> list[str]:
    """Paragraph-ish blocks, with contiguous table lines fused into one unsplittable block."""
    out: list[str] = []
    table: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        para = para.strip()
        if not para:
            continue
        if para.lstrip().startswith("|"):
            table.append(para)
            continue
        if table:
            out.append("\n\n".join(table))
            table = []
        out.append(para)
    if table:
        out.append("\n\n".join(table))
    return out


def split_oversized(heading: str, text: str) -> list[str]:
    """Pack blocks up to TARGET_TOKENS, carrying OVERLAP_TOKENS of tail into the next part."""
    if estimate_tokens(text) <= TARGET_TOKENS:
        return [text]

    parts: list[str] = []
    current: list[str] = []
    size = 0
    for block in _blocks(text):
        block_size = estimate_tokens(block)
        if current and size + block_size > TARGET_TOKENS:
            parts.append("\n\n".join(current))
            tail, tail_size = [], 0
            for previous in reversed(current):
                previous_size = estimate_tokens(previous)
                if tail_size + previous_size > OVERLAP_TOKENS:
                    break
                tail.insert(0, previous)
                tail_size += previous_size
            current, size = list(tail), tail_size
        current.append(block)
        size += block_size
    if current:
        parts.append("\n\n".join(current))
    return parts


def chunk_file(path: Path) -> list[Chunk]:
    raw = path.read_text(encoding="utf-8")
    meta, body = parse_front_matter(raw)
    source_id = meta.get("source_id") or path.stem
    tier = int(meta.get("tier", 2))
    updated_at = meta.get("updated_at", "")

    chunks: list[Chunk] = []
    for heading, text in split_sections(body):
        if estimate_tokens(text) < MIN_TOKENS:
            continue
        for i, part in enumerate(split_oversized(heading, text)):
            suffix = "" if i == 0 else f"-{i + 1}"
            chunks.append(
                Chunk(
                    id=f"{source_id}#{slug(heading)}{suffix}",
                    # The heading rides inside the text so that both the retriever and
                    # the answering model see what the passage is about.
                    text=f"{heading}\n\n{part}",
                    source_file=path.name,
                    heading=heading,
                    tier=tier,
                    updated_at=updated_at,
                )
            )
    return chunks


def chunk_corpus(raw_dir: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for path in sorted(raw_dir.glob("*.md")):
        if path.name.startswith(("README", "_")):
            continue
        chunks.extend(chunk_file(path))
    return chunks
