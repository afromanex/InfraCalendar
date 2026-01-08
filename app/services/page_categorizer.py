import re
from typing import Optional

from app.domain.page import Page


class PageCategorizer:
    """Heuristic page categorizer utilities."""

    ISO_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}(?:[T\s]\d{2}:\d{2}:?\d{0,2})?\b")
    MDY_RE = re.compile(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?'?\s+\d{1,2}(?:,?\s*\d{4})?\b", re.IGNORECASE)
    NUMERIC_RE = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
    YEAR_RE = re.compile(r"\b(?:19|20)\d{2}\b")
    WEEKDAY_RE = re.compile(r"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\b", re.IGNORECASE)
    TIME_RE = re.compile(r"\b\d{1,2}:\d{2}(?:\s?[APMapm]{2})?\b")
    KEYWORDS = re.compile(r"\b(calendar|event|events|schedule|agenda|meeting|starts|ends|date)\b", re.IGNORECASE)

    @classmethod
    def is_calendar(cls, page: Optional[Page] = None, text: Optional[str] = None) -> bool:
        """Return True if `page.plain_text` or `text` contains anything date-related.

        Accepts either a `Page` instance or a raw text string.
        """
        if page is not None:
            text = page.plain_text or ""
        if text is None:
            return False
        if not isinstance(text, str):
            return False

        # quick keyword check
        if cls.KEYWORDS.search(text):
            return True

        # date/time patterns
        if cls.ISO_RE.search(text):
            return True
        if cls.MDY_RE.search(text):
            return True
        if cls.NUMERIC_RE.search(text):
            return True
        if cls.WEEKDAY_RE.search(text):
            return True
        if cls.TIME_RE.search(text):
            return True
        if cls.YEAR_RE.search(text):
            return True

        return False
