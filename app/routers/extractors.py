from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.domain.event import Event
from app.repositories.pages import PagesRepository
from app.services.page_event_extract_and_save import PageEventService


class ExtractionResult(BaseModel):
    total_pages: int
    events_saved: int
    extraction_version: Optional[str] = None


class SingleExtractionResult(BaseModel):
    page_url: str
    event: Optional[dict] = None
    error: Optional[str] = None


class ExtractorsRouter:
    """Router for event extraction endpoints."""
    
    def __init__(
        self,
        pages_repo: PagesRepository,
        event_service: PageEventService
    ):
        """
        Initialize router with dependencies.
        
        Args:
            pages_repo: Repository for accessing pages
            event_service: Service for extracting and saving events
        """
        self.pages_repo = pages_repo
        self.event_service = event_service
        self.router = APIRouter(prefix="/extractors", tags=["Extractors"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all routes with the router."""
        self.router.add_api_route(
            "/extract",
            self.extract_events,
            methods=["POST"],
            response_model=ExtractionResult
        )
        self.router.add_api_route(
            "/extract-single",
            self.extract_single_event,
            methods=["GET"],
            response_model=SingleExtractionResult
        )
    
    async def extract_events(
        self,
        limit: Optional[int] = Query(None, description="Max number of pages to process"),
        config_id: Optional[str] = Query(None, description="Filter by config name (e.g., starkparks.yml)"),
        extraction_version: Optional[str] = Query("v1", description="Extraction version identifier")
    ) -> ExtractionResult:
        """
        Extract events from pages stored in the database.
        Processes pages and optionally saves extracted events to the database.
        """
        print(f"DEBUG: Starting extraction with limit={limit}, config_id={config_id}")
        
        # Get pages from database
        pages = self.pages_repo.fetch_pages(full=True, limit=limit, config_id=config_id)
        print(f"DEBUG: Fetched {len(pages)} pages from database")
        
        events_saved = 0
        for page in pages:
            # Extract and save event
            print(f"DEBUG: Extracting event from page_url={page.page_url}")
            event = await self.event_service.extract_and_save(page)

            if event is None:
                print(f"DEBUG: No event found from page_url={page.page_url}")
                continue 
            
            print(f"DEBUG: Found and saved event from page_url={page.page_url}")
            print(f"DEBUG: Event: {event}")
            events_saved += 1
            
        print(f"DEBUG: Extraction complete. Saved: {events_saved}")
        
        return ExtractionResult(
            total_pages=len(pages),
            events_saved=events_saved,
            extraction_version=extraction_version
        )

    async def extract_single_event(
        self,
        page_url: str = Query(..., description="URL of the page to extract event from")
    ) -> SingleExtractionResult:
        """
        Extract a single event from a page by URL.
        Useful for testing and debugging extraction without processing all pages.
        """
        print(f"DEBUG: Extracting single event from page_url={page_url}")
        
        # Get page from database by URL
        page = self.pages_repo.get_page_by_url(page_url)
        
        if page is None:
            raise HTTPException(
                status_code=404, 
                detail=f"Page not found in database: {page_url}"
            )
        
        # Extract and save event
        event = await self.event_service.extract_and_save(page)
        
        if event is None:
            return SingleExtractionResult(
                page_url=page_url,
                event=None,
                error="No event could be extracted from this page",
                saved=False
            )
        
        # Convert Event to dict for response
        event_dict = {
            "uid": event.uid,
            "dtstamp": event.dtstamp,
            "dtstart": event.dtstart,
            "dtend": event.dtend,
            "duration": event.duration,
            "summary": event.summary,
            "description": event.description,
            "location": event.location,
            "url": event.url,
            "categories": event.categories,
            "rrule": event.rrule,
            "title": event.title,
            "start": event.start,
            "raw": event.raw
        }
        
        print(f"DEBUG: Successfully extracted and saved event: {event.summary}")
        
        return SingleExtractionResult(
            page_url=page_url,
            event=event_dict,
            error=None,
            saved=True
        )


# Factory function to create router with dependencies from container
def create_extractors_router(container) -> APIRouter:
    """Create and configure the extractors router with dependencies from container."""
    extractors_router = ExtractorsRouter(
        pages_repo=container.pages_repository(),
        event_service=container.page_event_service()
    )
    return extractors_router.router


# Note: router is now initialized in main.py with container
router = None
