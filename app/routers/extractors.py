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
    save_to_db: bool = Query(True, description="Save extracted events to database"),
    extraction_version: Optional[str] = Query("v1", description="Extraction version identifier")
):
    """
    Extract events from pages stored in the database.
    Processes pages and optionally saves extracted events to the database.
    """
    try:
        print(f"DEBUG: Starting extraction with limit={limit}, config_id={config_id}, save_to_db={save_to_db}")
        pages_repo = PagesRepository()
        events_repo = EventsRepository()
        
        # Get pages from database
        pages = pages_repo.fetch_pages(full=True, limit=limit, config_id=config_id)
        print(f"DEBUG: Fetched {len(pages)} pages from database")
        
        events_saved = 0
        for page in pages:

            # Extract event from page
            print(f"DEBUG: Extracting event from page_url={page.page_url}")
            event = PageEventExtractor.extract_events(page)

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
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting events: {str(e)}")
