"""Extraction-coverage eval: compare a document's extracted equipment against a
ground-truth list of expected equipment names.

Usage (from backend/, venv python):

    python scripts/eval_extraction.py <document_id> [ground_truth.txt]
    python scripts/eval_extraction.py --latest-rfp [ground_truth.txt]

The ground-truth file has one expected equipment name per line (blank lines and
lines starting with '#' ignored). Matching is fuzzy: an expectation counts as
found when its canonicalized tokens overlap an extracted equipment label. The
script prints every extracted equipment (label, page, parameter count), then a
found/missing report and a recall percentage. Deterministic — no LLM involved.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg
from dotenv import load_dotenv

from app.services.matching.normalization import canonicalize_text

_STOPWORDS = {"for", "the", "a", "an", "of", "at", "with", "and", "or", "in", "to", "type"}


def _tokens(value: str) -> set[str]:
    return {token for token in canonicalize_text(value).split() if token not in _STOPWORDS}


def _matches(expected: str, extracted_labels: list[str]) -> str | None:
    """Return the extracted label matching the expectation, if any."""
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return None
    best: tuple[float, str] | None = None
    for label in extracted_labels:
        label_tokens = _tokens(label)
        if not label_tokens:
            continue
        overlap = len(expected_tokens & label_tokens)
        score = overlap / len(expected_tokens)
        if score > (best[0] if best else 0):
            best = (score, label)
    if best and best[0] >= 0.5:
        return best[1]
    return None


def main() -> int:
    load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))
    url = os.environ["ALEMBIC_DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")

    args = sys.argv[1:]
    if not args:
        print(__doc__)
        return 2
    ground_truth_path = args[1] if len(args) > 1 else None

    with psycopg.connect(url) as conn:
        cur = conn.cursor()
        if args[0] == "--latest-rfp":
            cur.execute(
                "select id, original_filename from documents where doc_type='rfp' "
                "order by created_at desc limit 1"
            )
            row = cur.fetchone()
            if row is None:
                print("No RFP documents found")
                return 1
            document_id, filename = str(row[0]), row[1]
        else:
            document_id = args[0]
            cur.execute("select original_filename from documents where id=%s", (document_id,))
            row = cur.fetchone()
            if row is None:
                print(f"Document {document_id} not found")
                return 1
            filename = row[0]

        cur.execute(
            "select r.equipment_label, r.source_page, "
            "(select count(*) from requirement_parameters rp where rp.requirement_id=r.id) "
            "from requirements r where r.document_id=%s order by r.source_page nulls last",
            (document_id,),
        )
        extracted = cur.fetchall()
        cur.execute("select structure_analysis from documents where id=%s", (document_id,))
        structure = cur.fetchone()[0]

    print(f"Document: {filename} ({document_id})")
    print(f"\nExtracted equipment ({len(extracted)}):")
    for label, page, param_count in extracted:
        print(f"  p{page or '?':>3}  {label}  [{param_count} params]")

    if structure:
        print(
            f"\nStructure pass: {len(structure.get('selected_pages', []))}/"
            f"{structure.get('page_count', '?')} pages selected "
            f"({structure.get('technical_pages', '?')} technical, "
            f"{structure.get('excluded_pages', '?')} excluded, "
            f"{structure.get('uncovered_pages_included', '?')} uncovered included)"
        )

    if not ground_truth_path:
        return 0

    with open(ground_truth_path, encoding="utf-8") as handle:
        expectations = [
            line.strip() for line in handle if line.strip() and not line.strip().startswith("#")
        ]
    labels = [label for label, _, _ in extracted]
    found: list[tuple[str, str]] = []
    missing: list[str] = []
    for expected in expectations:
        match = _matches(expected, labels)
        if match:
            found.append((expected, match))
        else:
            missing.append(expected)

    print(f"\nGround truth: {len(expectations)} expected equipment")
    print(f"Found {len(found)}/{len(expectations)} ({100 * len(found) // len(expectations)}% recall)")
    if missing:
        print("\nMISSING:")
        for expected in missing:
            print(f"  - {expected}")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
