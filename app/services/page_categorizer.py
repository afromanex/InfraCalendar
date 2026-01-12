import re
from typing import Optional

from app.clients.ollama_client import OllamaClient
from app.domain.page import Page
from app.domain.event import Event


class PageCategorizer:
    """Heuristic page categorizer utilities."""
    @classmethod
    def is_calendar(cls, page: Optional[Page] = None) -> bool:
        client = OllamaClient()

        is_event = client.chat_is_event(page)
        
        return is_event
    
    @staticmethod
    def is_valid_event(ev: Event) -> bool:
        """Check if extracted event is valid and substantial."""
        if ev is None:
            return False
        
        if ev.title is None or ev.start is None:
            return False
        
        has_location = ev.location is not None
        has_description = ev.description is not None and len(ev.description) >= 10
        
        return has_location or has_description