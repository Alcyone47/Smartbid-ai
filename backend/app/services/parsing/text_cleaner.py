import re


class TextCleaner:
    """Normalizes raw extracted page text before it's sent to the LLM (whitespace, control chars, blank-line runs)."""

    _WHITESPACE_RE = re.compile(r"[ \t]+")
    _BLANK_LINES_RE = re.compile(r"\n{3,}")

    def clean_page(self, text: str) -> str:
        text = text.replace("\x00", "")
        text = self._WHITESPACE_RE.sub(" ", text)
        text = self._BLANK_LINES_RE.sub("\n\n", text)
        return text.strip()

    def clean_pages(self, pages: list[str]) -> list[str]:
        return [self.clean_page(page) for page in pages]
