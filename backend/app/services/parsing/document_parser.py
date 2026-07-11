from dataclasses import dataclass

from app.core.exceptions import UnsupportedDocumentTypeError
from app.services.parsing.docx import extract_docx_pages
from app.services.parsing.pdf import extract_pdf_pages

PDF_MIME_TYPES = {"application/pdf"}
DOCX_MIME_TYPES = {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@dataclass
class ParsedDocument:
    pages: list[str]
    page_count: int


class DocumentParser:
    """Routes a document's raw bytes to the right per-format extractor and returns per-page text."""

    def parse(self, content: bytes, mime_type: str) -> ParsedDocument:
        if mime_type in PDF_MIME_TYPES:
            pages = extract_pdf_pages(content)
        elif mime_type in DOCX_MIME_TYPES:
            pages = extract_docx_pages(content)
        else:
            raise UnsupportedDocumentTypeError(f"Unsupported document mime type: {mime_type}")
        return ParsedDocument(pages=pages, page_count=len(pages))
