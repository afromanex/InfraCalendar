from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from pydantic import BaseModel

from app.repositories.events import EventsRepository
from app.services.ical_formatting_service import ICalFormattingService
from app.domain.event import Event


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


class CalendarsRouter:
    """Router for calendar export endpoints."""
    
    def __init__(
        self,
        events_repo: EventsRepository,
        ical_service: ICalFormattingService
    ):
        """
        Initialize router with dependencies.
        
        Args:
            events_repo: Repository for accessing events
            ical_service: Service for formatting iCalendar output
        """
        self.events_repo = events_repo
        self.ical_service = ical_service
        self.router = APIRouter(prefix="/calendars", tags=["Calendars"])
        self._register_routes()
    
    def _register_routes(self):
        """Register all routes with the router."""
        self.router.add_api_route(
            "/{config_id}/events",
            self.get_events_by_config,
            methods=["GET"],
            response_model=List[EventResponse]
        )
        self.router.add_api_route(
            "/{config_id}/ical",
            self.get_ical_by_config,
            methods=["GET"]
        )
    
    async def get_events_by_config(self, config_id: str) -> List[EventResponse]:
        """
        Get all events associated with a config name as JSON.
        
        Returns:
            List of events in JSON format
        """
        # Get all events for this config
        events = self.events_repo.get_events_by_config_id(config_id, only_valid=True)
        
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

    async def get_ical_by_config(self, config_id: str) -> Response:
        """
        Generate an iCalendar (.ics) file for all events associated with a config name.
        
        Returns:
            iCalendar formatted text file with all events from pages with the specified config
        """
        # Get all events for this config
        events = self.events_repo.get_events_by_config_id(config_id, only_valid=True)
        
        if not events:
            raise HTTPException(status_code=404, detail=f"No events found for config_id={config_id}")
        
        # Generate iCalendar content
        ical_content = self.ical_service.format_ical(
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


# Factory function to create router with dependencies from container
def create_calendars_router(container) -> APIRouter:
    """Create and configure the calendars router with dependencies from container."""
    calendars_router = CalendarsRouter(
        events_repo=container.events_repository(),
        ical_service=container.ical_formatting_service()
    )
    return calendars_router.router


# Note: router is now initialized in main.py with container
router = None
