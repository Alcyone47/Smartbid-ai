import io

from docx import Document as DocxDocument


def extract_docx_pages(content: bytes) -> list[str]:
    """python-docx has no concept of page boundaries, so the whole document is returned as a single page."""
    document = DocxDocument(io.BytesIO(content))
    text = "\n".join(paragraph.text for paragraph in document.paragraphs)
    return [text]
