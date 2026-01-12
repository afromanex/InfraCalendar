from typing import Optional

from app.domain.event import Event
from app.domain.page import Page
from app.repositories.events import EventsRepository
from app.services.page_event_extractor import PageEventExtractor
from app.services.page_categorizer import PageCategorizer


class PageEventService:
    """Service for extracting and persisting events from pages."""
    
    def __init__(
        self,
        events_repository: EventsRepository,
        extractor: PageEventExtractor,
        categorizer: PageCategorizer
    ):
        """
        Initialize the service with dependencies.
        
        Args:
            events_repository: Repository for persisting events
            extractor: PageEventExtractor instance
            categorizer: PageCategorizer instance
        """
        self.events_repo = events_repository
        self.extractor = extractor
        self.categorizer = categorizer
    
    async def extract_and_save(self, page: Page) -> Optional[Event]:
        """
        Extract an event from a page and save it to the database.
        
        Args:
            page: The Page object to extract an event from
            
        Returns:
            The extracted and saved Event object, or None if no valid event could be extracted
        """
        # Extract event from page
        event = await self.extractor.extract_events_async(page)
        
        if event is None or not self.categorizer.is_valid_event(event):
            return None
        
        # Save to database
        self.events_repo.upsert_event_by_hash(event, page.page_id)
        
        return event
