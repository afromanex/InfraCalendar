from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel

from app.domain.event import Event
from app.repositories.pages import PagesRepository
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
    config_id: Optional[int] = Query(None, description="Filter by config_id")
):
    """
    Extract events from pages stored in the database.
    Processes pages and returns extracted events.
    """
    try:
        pages_repo = PagesRepository()
        
        # Get pages from database
        pages = pages_repo.fetch_pages(full=True, limit=limit, config_id=config_id)
        
        extracted_events = []
        pages_without_events = 0
        
        for page in pages:
            try:
                # Extract event from page
                event = PageEventExtractor.extract_events(page)
                
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
                else:
                    pages_without_events += 1
            except Exception as e:
                # Log error but continue processing
                print(f"Error extracting event from page {page.page_url}: {str(e)}")
                pages_without_events += 1
        
        return ExtractionResult(
            total_pages=len(pages),
            events_extracted=len(extracted_events),
            pages_without_events=pages_without_events,
            events=extracted_events
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error extracting events: {str(e)}")
