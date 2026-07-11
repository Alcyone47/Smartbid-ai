import io

from pypdf import PdfReader


def extract_pdf_pages(content: bytes) -> list[str]:
    reader = PdfReader(io.BytesIO(content))
    return [page.extract_text() or "" for page in reader.pages]
