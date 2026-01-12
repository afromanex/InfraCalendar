import re
from typing import Optional

from app.clients.ollama_client import OllamaClient
from app.domain.page import Page
from app.domain.event import Event


class PageCategorizer:
    """Heuristic page categorizer utilities."""
    
    def __init__(self, ollama_client: OllamaClient, min_description_length: int = 10):
        """
        Initialize with dependencies.
        
        Args:
            ollama_client: Client for communicating with Ollama
            min_description_length: Minimum description length for valid events
        """
        self.ollama_client = ollama_client
        self.min_description_length = min_description_length
    
    def is_valid_event(self, ev: Event) -> bool:
        """Check if extracted event is valid and substantial."""
        if ev is None:
            return False
        
        if ev.title is None or ev.start is None:
            return False
        
        has_location = ev.location is not None
        has_description = ev.description is not None and len(ev.description) >= self.min_description_length
        
        return has_location or has_description