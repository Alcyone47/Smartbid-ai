import io
from collections import Counter, defaultdict

import pdfplumber

from app.services.parsing.outline import HeadingHint

# A heading line must be no longer than this (headings are short); longer lines
# are treated as body text even if they happen to be bold/large.
_MAX_HEADING_WORDS = 12
# A line qualifies as a heading if its font is at least this many points larger
# than the document's body font size.
_HEADING_SIZE_MARGIN = 0.5
_BOLD_MARKERS = ("bold", "black", "semibold", "heavy")


def extract_pdf_pages(content: bytes) -> list[str]:
    """One text string per PDF page (flowing text + pipe-flattened tables)."""
    pages, _outline = extract_pdf_document(content)
    return pages


def extract_pdf_document(content: bytes) -> tuple[list[str], list[HeadingHint]]:
    """Extract per-page text and candidate section headings in one pdfplumber pass.

    pdfplumber (MIT, built on pdfminer.six) handles column layout and tables far
    better than the previous pypdf reader. Table rows are appended after the page's
    flowing text so tabular specs aren't lost. Headings are inferred from font
    size/weight relative to the document's dominant body font — these feed the
    semantic structure-analysis pass and are never persisted.
    """
    pages: list[str] = []
    # (page_number, [(text, size, fontname)]) captured per line for a second pass
    # once the document-wide body font size is known.
    page_lines: list[tuple[int, list[tuple[str, float, str]]]] = []
    size_counter: Counter[int] = Counter()

    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for index, page in enumerate(pdf.pages):
            page_number = index + 1
            parts: list[str] = []
            text = page.extract_text() or ""
            if text:
                parts.append(text)
            for table in page.extract_tables() or []:
                for row in table:
                    cells = [cell.strip() for cell in row if cell and cell.strip()]
                    if cells:
                        parts.append(" | ".join(cells))
            pages.append("\n".join(parts))

            lines = _page_lines(page)
            page_lines.append((page_number, lines))
            for _line_text, size, _fontname in lines:
                if size:
                    size_counter[round(size)] += 1

    body_size = float(size_counter.most_common(1)[0][0]) if size_counter else 0.0
    outline = _detect_headings(page_lines, body_size)
    return pages, outline


def _page_lines(page) -> list[tuple[str, float, str]]:
    """Group a page's words into visual lines with their max font size and fonts."""
    try:
        words = page.extract_words(extra_attrs=["size", "fontname"]) or []
    except Exception:
        # Some malformed PDFs raise inside pdfminer on word extraction; headings
        # are best-effort, so degrade to no headings for this page.
        return []

    grouped: dict[int, list[dict]] = defaultdict(list)
    for word in words:
        # Round the vertical position so words on the same line group together.
        grouped[round(word.get("top", 0) / 2)].append(word)

    lines: list[tuple[str, float, str]] = []
    for _top, line_words in sorted(grouped.items()):
        line_words.sort(key=lambda w: w.get("x0", 0))
        line_text = " ".join(w.get("text", "") for w in line_words).strip()
        if not line_text:
            continue
        sizes = [w.get("size", 0) for w in line_words if w.get("size")]
        max_size = max(sizes) if sizes else 0.0
        fonts = " ".join(w.get("fontname", "") for w in line_words).lower()
        lines.append((line_text, max_size, fonts))
    return lines


def _detect_headings(
    page_lines: list[tuple[int, list[tuple[str, float, str]]]], body_size: float
) -> list[HeadingHint]:
    headings: list[HeadingHint] = []
    for page_number, lines in page_lines:
        for line_text, max_size, fonts in lines:
            if len(line_text.split()) > _MAX_HEADING_WORDS:
                continue
            if line_text.endswith((".", ",", ";")):
                continue
            is_bold = any(marker in fonts for marker in _BOLD_MARKERS)
            is_larger = bool(body_size) and max_size >= body_size + _HEADING_SIZE_MARGIN
            if is_larger or is_bold:
                headings.append(
                    HeadingHint(
                        text=line_text,
                        page=page_number,
                        font_size=round(max_size, 1) if max_size else None,
                        is_bold=is_bold,
                    )
                )
    return headings
