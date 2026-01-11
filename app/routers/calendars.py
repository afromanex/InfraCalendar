from fastapi import APIRouter, HTTPException, Response

from app.repositories.events import EventsRepository
from app.services.ical_formatting_service import ICalFormattingService

router = APIRouter(prefix="/calendars", tags=["Calendars"])


@router.get("/ical/{config_id}")
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
