from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from pydantic import BaseModel

from app.repositories.events import EventsRepository
from app.services.ical_formatting_service import ICalFormattingService
from app.domain.event import Event

router = APIRouter(prefix="/calendars", tags=["Calendars"])


class EventResponse(BaseModel):
    uid: Optional[str] = None
    dtstart: Optional[str] = None
    dtend: Optional[str] = None
    duration: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    categories: Optional[list] = []
    rrule: Optional[str] = None
    title: Optional[str] = None
    start: Optional[str] = None


@router.get("/{config_id}/events", response_model=List[EventResponse])
async def get_events_by_config(config_id: int):
    """
    Get all events associated with a config_id as JSON.
    
    Returns:
        List of events in JSON format
    """
    events_repo = EventsRepository()
    
    # Get all events for this config_id
    events = events_repo.get_events_by_config_id(config_id, only_valid=True)
    
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for config_id={config_id}")
    
    # Convert to response format
    return [
        EventResponse(
            uid=event.uid,
            dtstart=event.dtstart,
            dtend=event.dtend,
            duration=event.duration,
            summary=event.summary,
            description=event.description,
            location=event.location,
            url=event.url,
            categories=event.categories or [],
            rrule=event.rrule,
            title=event.title,
            start=event.start
        )
        for event in events
    ]


@router.get("/{config_id}/ical")
async def get_ical_by_config(config_id: int):
    """
    Generate an iCalendar (.ics) file for all events associated with a config_id.
    
    Returns:
        iCalendar formatted text file with all events from pages with the specified config_id
    """
    events_repo = EventsRepository()
    
    # Get all events for this config_id
    events = events_repo.get_events_by_config_id(config_id, only_valid=True)
    
    if not events:
        raise HTTPException(status_code=404, detail=f"No events found for config_id={config_id}")
    
    # Generate iCalendar content
    ical_content = ICalFormattingService.format_ical(
        events, 
        calendar_name=f"InfraCalendar-{config_id}"
    )
    
    # Return as downloadable .ics file
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=calendar-{config_id}.ics"
        }
    )
