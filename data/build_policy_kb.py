"""Build a typed, versioned clause list from the source policy PDF.

Splits each page's extracted text on its `POLICY: <title>` headings — the
document's own structure, not a heuristic — and writes one `PolicyClause` per
heading, carrying the page it came from. `reference/` is local-only
(gitignored, see NOTICE.md); the output is committed so a fresh clone runs
without it, the same precedent as A7's `data/rulebook.json`.
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

from pypdf import PdfReader

from sentinel.store.models import PolicyClause

SOURCE_PDF = Path("reference/session_files_telecom/policy_kb.pdf")
OUTPUT = Path("data/policy_clauses.json")

_HEADING = re.compile(r"POLICY:\s*(.+)")


def _slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return f"clause-{slug}"


def _clean(text: str) -> str:
    """Decomposes PDF ligature glyphs (`ﬁ` -> `fi`, `ﬀ` -> `ff`) that
    `extract_text` leaves as single codepoints."""
    return unicodedata.normalize("NFKD", text)


def parse_pdf(path: Path) -> list[PolicyClause]:
    """A clause's body commonly continues onto the next page with no repeated
    heading (the source PDF wraps "Account Management" this way), so state
    carries across the whole document rather than resetting per page."""
    reader = PdfReader(path)
    clauses: list[PolicyClause] = []
    current_title: str | None = None
    current_title_page = 0
    current_body: list[str] = []

    def _flush() -> None:
        if current_title is None:
            return
        title = _clean(current_title)
        body_text = _clean(" ".join(line.strip() for line in current_body if line.strip()))
        clauses.append(
            PolicyClause(
                clause_id=_slugify(title),
                title=title,
                body=body_text,
                page=current_title_page,
            )
        )

    for page_number, page in enumerate(reader.pages, start=1):
        for line in (page.extract_text() or "").splitlines():
            match = _HEADING.match(line.strip())
            if match:
                _flush()
                current_title = match.group(1).strip()
                current_title_page = page_number
                current_body = []
            else:
                current_body.append(line)
    _flush()

    return clauses


def main() -> int:
    if not SOURCE_PDF.exists():
        print(
            f"Source PDF not found at {SOURCE_PDF} — reference/ is local-only "
            "(see NOTICE.md). If you have the source material, place it there; "
            f"otherwise the committed {OUTPUT} is already current.",
            file=sys.stderr,
        )
        return 1

    clauses = parse_pdf(SOURCE_PDF)
    if len(clauses) < 6:
        print(
            f"Expected at least 6 policy clauses, parsed {len(clauses)} "
            "— check the PDF text extraction."
        )
        return 1

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps([c.model_dump(mode="json") for c in clauses], indent=2) + "\n")
    print(f"Wrote {len(clauses)} clauses to {OUTPUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
