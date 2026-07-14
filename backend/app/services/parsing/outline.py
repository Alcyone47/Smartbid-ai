from dataclasses import dataclass


@dataclass
class HeadingHint:
    """A candidate section heading detected from document layout.

    Used only to build the compact structure digest fed to the semantic
    structure-analysis pass; never persisted. ``font_size``/``is_bold`` are the
    layout signals that flagged the line as a heading (absent for DOCX, which is
    detected by paragraph style instead).
    """

    text: str
    page: int
    font_size: float | None = None
    is_bold: bool = False
