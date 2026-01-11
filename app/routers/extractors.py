from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.domain.event import Event
from app.repositories.pages import PagesRepository
from app.repositories.events import EventsRepository
from app.services.page_event_extractor import PageEventExtractor

router = APIRouter(prefix="/extractors", tags=["Extractors"])

class ExtractionResult(BaseModel):
    total_pages: int
    events_saved: int
    extraction_version: Optional[str] = None

class SingleExtractionResult(BaseModel):
    page_url: str
    event: Optional[dict] = None
    error: Optional[str] = None

def is_valid_event(ev: Event) -> bool:
    """Check if extracted event is valid and substantial."""
    if ev is None:
        return False
    
    if ev.title is None or ev.start is None:
        return False
    
    has_location = ev.location is not None
    has_description = ev.description is not None and len(ev.description) >= 40
    
    return has_location or has_description


@router.post("/extract", response_model=ExtractionResult)
async def extract_events(
    limit: Optional[int] = Query(None, description="Max number of pages to process"),
    config_id: Optional[int] = Query(None, description="Filter by config_id"),
    extraction_version: Optional[str] = Query("v1", description="Extraction version identifier")
):
    """
    Extract events from pages stored in the database.
    Processes pages and optionally saves extracted events to the database.
    """
    print(f"DEBUG: Starting extraction with limit={limit}, config_id={config_id}")
    pages_repo = PagesRepository()
    events_repo = EventsRepository()
    
    # Get pages from database
    pages = pages_repo.fetch_pages(full=True, limit=limit, config_id=config_id)
    print(f"DEBUG: Fetched {len(pages)} pages from database")
    
    events_saved = 0
    for page in pages:

        # Extract event from page
        print(f"DEBUG: Extracting event from page_url={page.page_url}")
        event = await PageEventExtractor.extract_events_async(page)

        if is_valid_event(event) == False:
            print(f"DEBUG: No event found from page_url={page.page_url}")
            continue 
        
        print(f"DEBUG: Found from page_url={page.page_url}")
        print(f"DEBUG: Event: {event}")

        events_repo.upsert_event_by_hash(event)
        events_saved += 1
        
    print(f"DEBUG: Extraction complete. Saved: {events_saved}")
    
    return ExtractionResult(
        total_pages=len(pages),
        events_saved=events_saved,
        extraction_version=extraction_version
    )


@router.get("/extract-single", response_model=SingleExtractionResult)
async def extract_single_event(
    page_url: str = Query(..., description="URL of the page to extract event from")
):
    """
    Extract a single event from a page by URL.
    Useful for testing and debugging extraction without processing all pages.
    """
    print(f"DEBUG: Extracting single event from page_url={page_url}")
    pages_repo = PagesRepository()
    
    # Get page from database by URL
    page = pages_repo.get_page_by_url(page_url)
    
    if page is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Page not found in database: {page_url}"
        )
    
    # Extract event from page
    event = await PageEventExtractor.extract_events_async(page)
    
    if event is None:
        return SingleExtractionResult(
            page_url=page_url,
            event=None,
            error="No event could be extracted from this page"
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
    
    print(f"DEBUG: Successfully extracted event: {event.summary}")
    
    return SingleExtractionResult(
        page_url=page_url,
        event=event_dict,
        error=None
    )
    
        
