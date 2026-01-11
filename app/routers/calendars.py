from fastapi import APIRouter, HTTPException, Response
from datetime import datetime
from typing import List

from app.repositories.events import EventsRepository
from app.domain.event import Event

router = APIRouter(prefix="/calendars", tags=["Calendars"])


def generate_ical(events: List[Event], calendar_name: str = "InfraCalendar") -> str:
    """Generate iCalendar format from events."""
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:-//InfraCalendar//EN",
        f"X-WR-CALNAME:{calendar_name}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]
    
    for event in events:
        lines.append("BEGIN:VEVENT")
        
        # UID - use event URL as unique identifier
        if event.url:
            lines.append(f"UID:{event.url}")
        
        # DTSTAMP - timestamp when event was created/modified
        if event.dtstamp:
            lines.append(f"DTSTAMP:{event.dtstamp}")
        else:
            lines.append(f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}")
        
        # DTSTART - event start date/time
        if event.dtstart:
            # Format: YYYYMMDD or YYYYMMDDTHHMMSS
            dtstart = str(event.dtstart).replace("-", "").replace(":", "").replace(" ", "T")
            if "T" not in dtstart:
                lines.append(f"DTSTART;VALUE=DATE:{dtstart}")
            else:
                lines.append(f"DTSTART:{dtstart}")
        
        # DTEND - event end date/time
        if event.dtend:
            dtend = str(event.dtend).replace("-", "").replace(":", "").replace(" ", "T")
            if "T" not in dtend:
                lines.append(f"DTEND;VALUE=DATE:{dtend}")
            else:
                lines.append(f"DTEND:{dtend}")
        
        # SUMMARY - event title
        if event.summary:
            lines.append(f"SUMMARY:{event.summary}")
        
        # DESCRIPTION - event description
        if event.description:
            # Escape special characters and wrap long lines
            desc = event.description.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")
            lines.append(f"DESCRIPTION:{desc}")
        
        # LOCATION - event location
        if event.location:
            lines.append(f"LOCATION:{event.location}")
        
        # URL - event URL
        if event.url:
            lines.append(f"URL:{event.url}")
        
        # CATEGORIES
        if event.categories:
            cats = ",".join(event.categories) if isinstance(event.categories, list) else str(event.categories)
            lines.append(f"CATEGORIES:{cats}")
        
        # RRULE - recurrence rule
        if event.rrule:
            lines.append(f"RRULE:{event.rrule}")
        
        lines.append("END:VEVENT")
    
    lines.append("END:VCALENDAR")
    
    return "\r\n".join(lines)


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
    ical_content = generate_ical(events, calendar_name=f"InfraCalendar-{config_id}")
    
    # Return as downloadable .ics file
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=calendar-{config_id}.ics"
        }
    )
