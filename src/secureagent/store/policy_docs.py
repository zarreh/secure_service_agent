"""The policy knowledge base: markdown files with a small front matter block.

Read-only. A document is *data*; nothing here interprets its contents. The
document flagged `fixture_kind` is the planted indirect-injection payload
(docs/PLAN.md §6.1), findable by that flag without string-matching the body.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PolicyDoc:
    doc_id: str
    title: str
    body: str
    fixture_kind: str | None


def _parse(path: Path) -> PolicyDoc:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        raise ValueError(f"{path.name}: missing front matter")
    header, _, body = text[4:].partition("\n---\n")
    fields = dict(line.split(": ", 1) for line in header.splitlines() if ": " in line)
    for required in ("id", "title"):
        if required not in fields:
            raise ValueError(f"{path.name}: front matter lacks {required!r}")
    return PolicyDoc(fields["id"], fields["title"], body.strip(), fields.get("fixture_kind"))


def load_policy_docs(directory: Path) -> list[PolicyDoc]:
    return [_parse(path) for path in sorted(directory.glob("*.md"))]
