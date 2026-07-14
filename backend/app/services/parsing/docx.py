import io

from docx import Document as DocxDocument


def extract_docx_pages(content: bytes) -> list[str]:
    """python-docx has no concept of page boundaries, so the whole document is
    returned as a single page. Paragraph text plus table cell text are captured so
    spec tables (common in datasheets) are not dropped."""
    document = DocxDocument(io.BytesIO(content))
    parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text.strip()]
    for table in document.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return ["\n".join(parts)]
