from datetime import datetime
from typing import List

from app.domain.event import Event


class ICalFormattingService:
    """Service for formatting events into iCalendar format."""
    
    @staticmethod
    def format_ical(events: List[Event], calendar_name: str = "InfraCalendar") -> str:
        """
        Generate iCalendar format from events.
        
        Args:
            events: List of Event objects to format
            calendar_name: Name of the calendar
            
        Returns:
            iCalendar formatted string
        """
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


__all__ = ["ICalFormattingService"]
