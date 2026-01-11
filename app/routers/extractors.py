from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.domain.event import Event
from app.repositories.pages import PagesRepository
from app.repositories.events import EventsRepository
from app.services.page_event_extractor import PageEventExtractor

router = APIRouter(prefix="/extractors", tags=["Extractors"])


class ExtractedEvent(BaseModel):
    page_url: str
    page_id: Optional[int]
    title: Optional[str]
    start: Optional[str]
    end: Optional[str]
    location: Optional[dict]
    description: Optional[str]
    
    class Config:
        from_attributes = True


class ExtractionResult(BaseModel):
    total_pages: int
    events_extracted: int
    events_saved: int
    pages_without_events: int
    events: List[ExtractedEvent]


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
        
        extracted_events = []
        pages_without_events = 0
        events_saved = 0
        
        for idx, page in enumerate(pages):
            print(f"DEBUG: [{idx+1}/{len(pages)}] Processing: {page.page_url}")
            try:
                # Extract event from page
                print(f"DEBUG: About to call PageEventExtractor.extract_events")
                event = PageEventExtractor.extract_events(page)
                print(f"DEBUG: Extraction returned: event={event}, type={type(event)}")
                if event:
                    print(f"DEBUG: Event fields - title={event.title}, start={event.start}, location={event.location}")
                
                if is_valid_event(event):
                    extracted_events.append(ExtractedEvent(
                        page_url=page.page_url,
                        page_id=page.page_id,
                        title=event.title,
                        start=event.start,
                        end=event.end,
                        location=event.location,
                        description=event.description
                    ))
                    
                    # Save to database if requested
                    if save_to_db and page.page_id:
                        events_repo.upsert_event_by_hash(
                            event=event,
                            page_id=page.page_id,
                            extraction_version=extraction_version
                        )
                        events_saved += 1
                else:
                    pages_without_events += 1
            except Exception as e:
                # Log error but continue processing
                print(f"ERROR: Exception extracting event from page {page.page_url}")
                print(f"ERROR: Exception type: {type(e).__name__}")
                print(f"ERROR: Exception message: {str(e)}")
                import traceback
                print(f"ERROR: Traceback: {traceback.format_exc()}")
                pages_without_events += 1
        
        print(f"DEBUG: Extraction complete. Saved: {events_saved}")
        
        return ExtractionResult(
            total_pages=len(pages),
            events_extracted=len(extracted_events),
            events_saved=events_saved,
            pages_without_events=pages_without_events,
            events=extracted_events
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting events: {str(e)}")
