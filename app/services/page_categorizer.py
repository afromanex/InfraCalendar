import re
from typing import Optional

from app.clients.ollama_client import OllamaClient
from app.domain.page import Page


class PageCategorizer:
    """Heuristic page categorizer utilities."""
    @classmethod
    def is_calendar(cls, page: Optional[Page] = None) -> bool:
        client = OllamaClient()

        is_event = client.chat_is_event(page)
        
        return is_event