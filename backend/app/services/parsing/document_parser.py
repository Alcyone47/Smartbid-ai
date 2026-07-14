from dataclasses import dataclass, field

from app.core.exceptions import UnsupportedDocumentTypeError
from app.services.parsing.docx import extract_docx_document
from app.services.parsing.outline import HeadingHint
from app.services.parsing.pdf import extract_pdf_document

PDF_MIME_TYPES = {"application/pdf"}
DOCX_MIME_TYPES = {"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@dataclass
class ParsedDocument:
    pages: list[str]
    page_count: int
    # Candidate section headings detected from layout (font size/weight for PDF,
    # paragraph style for DOCX). Used to build the structure-analysis digest; may
    # be empty for text-only or image-only documents.
    outline: list[HeadingHint] = field(default_factory=list)


class DocumentParser:
    """Routes a document's raw bytes to the right per-format extractor and returns per-page text plus a heading outline."""

    def parse(self, content: bytes, mime_type: str) -> ParsedDocument:
        if mime_type in PDF_MIME_TYPES:
            pages, outline = extract_pdf_document(content)
        elif mime_type in DOCX_MIME_TYPES:
            pages, outline = extract_docx_document(content)
        else:
            raise UnsupportedDocumentTypeError(f"Unsupported document mime type: {mime_type}")
        return ParsedDocument(pages=pages, page_count=len(pages), outline=outline)
