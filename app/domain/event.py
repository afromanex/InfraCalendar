from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Event:
    # iCalendar-like fields (snake_case)
    uid: Optional[str] = None
    dtstamp: Optional[str] = None
    dtstart: Optional[str] = None
    dtend: Optional[str] = None
    duration: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    url: Optional[str] = None
    geo: Optional[str] = None
    categories: List[str] = field(default_factory=list)
    status: Optional[str] = None
    transp: Optional[str] = None
    sequence: Optional[int] = None
    created: Optional[str] = None
    last_modified: Optional[str] = None
    organizer: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    attach: List[str] = field(default_factory=list)
    classification: Optional[str] = None
    priority: Optional[int] = None
    rrule: Optional[str] = None
    rdate: List[str] = field(default_factory=list)
    exdate: List[str] = field(default_factory=list)
    recurrence_id: Optional[str] = None
    tzid: Optional[str] = None
    alarms: List[Dict[str, Any]] = field(default_factory=list)

    # raw payload and backward-compatible fields
    raw: Optional[str] = None
    # keep `title` and `start` for existing code compatibility
    title: Optional[str] = None
    start: Optional[str] = None
