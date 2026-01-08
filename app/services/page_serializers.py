from typing import Any, Dict

from app.domain.page import Page


class PageSerializer:
    @staticmethod
    def from_dict(d: Dict[str, Any]) -> Page:
        """Convert a mapping (e.g., parsed JSON line) to a `Page` domain object."""
        return Page(
            page_id=d.get("page_id"),
            page_url=d.get("page_url"),
            http_status=d.get("http_status"),
            fetched_at=d.get("fetched_at"),
            config_id=d.get("config_id"),
            plain_text=d.get("plain_text"),
        )
