from typing import List, Optional, Dict, Any

import dateparser.search


class PageDateService:
    """Service for extracting date/time mentions from free-form page text.

    Uses `dateparser.search.search_dates` to find date-like substrings and
    returns normalized results (ISO + dt object).
    """

    @classmethod
    def find_dates(cls, text: str, languages: Optional[List[str]] = None, settings: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Return a list of matches with keys: `text`, `dt` (ISO string), `dt_obj`.

        - `languages`: optional list of language codes to pass to dateparser.
        - `settings`: optional settings dict for dateparser.search.search_dates.
        """
        if not text:
            return []

        settings = settings or {"PREFER_DAY_OF_MONTH": "first"}
        try:
            results = dateparser.search.search_dates(text, languages=languages, settings=settings)
        except Exception:
            return []

        out: List[Dict[str, Any]] = []
        if not results:
            return out

        for matched, dt in results:
            iso = None
            try:
                iso = dt.isoformat()
            except Exception:
                iso = None

            out.append({"text": matched, "dt": iso, "dt_obj": dt})

        return out


__all__ = ["PageDateService"]
