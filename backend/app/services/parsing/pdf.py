import io

import pdfplumber


def extract_pdf_pages(content: bytes) -> list[str]:
    """One text string per PDF page via pdfplumber.

    pdfplumber (MIT, built on pdfminer.six) handles column layout and tables far
    better than the previous pypdf reader. Table rows are appended after the page's
    flowing text so tabular specs aren't lost.
    """
    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
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
    return pages
