from typing import Optional, List
import hashlib
import json
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Event as DBEvent
from app.domain.event import Event
from app.db.engine import make_engine


class EventsRepository:
    def __init__(self, engine=None):
        self.engine = engine or make_engine()

    def get_session(self) -> Session:
        return Session(self.engine)

    def _compute_hash(self, event: Event) -> str:
        """Compute a hash of event content to detect duplicates."""
        content = f"{event.title}|{event.start}|{event.dtstart}|{event.summary}|{event.location}|{event.url}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _domain_to_db(self, event: Event, page_id: int, extraction_version: Optional[str] = None) -> DBEvent:
        """Convert domain Event to database Event."""
        return DBEvent(
            page_id=page_id,
            uid=event.uid,
            dtstamp=event.dtstamp,
            dtstart=event.dtstart,
            dtend=event.dtend,
            duration=event.duration,
            summary=event.summary,
            description=event.description,
            location=event.location,
            url=event.url,
            geo=event.geo,
            categories=event.categories if event.categories else None,
            status=event.status,
            transp=event.transp,
            sequence=event.sequence,
            created=event.created,
            last_modified=event.last_modified,
            organizer=event.organizer,
            attendees=event.attendees if event.attendees else None,
            attach=event.attach if event.attach else None,
            classification=event.classification,
            priority=event.priority,
            rrule=event.rrule,
            rdate=event.rdate if event.rdate else None,
            exdate=event.exdate if event.exdate else None,
            recurrence_id=event.recurrence_id,
            tzid=event.tzid,
            alarms=event.alarms if event.alarms else None,
            raw=event.raw,
            title=event.title,
            start=event.start,
            extraction_version=extraction_version,
            content_hash=self._compute_hash(event),
            is_valid=self._is_valid_event(event)
        )

    def _db_to_domain(self, db_event: DBEvent) -> Event:
        """Convert database Event to domain Event."""
        return Event(
            uid=db_event.uid,
            dtstamp=db_event.dtstamp,
            dtstart=db_event.dtstart,
            dtend=db_event.dtend,
            duration=db_event.duration,
            summary=db_event.summary,
            description=db_event.description,
            location=db_event.location,
            url=db_event.url,
            geo=db_event.geo,
            categories=db_event.categories or [],
            status=db_event.status,
            transp=db_event.transp,
            sequence=db_event.sequence,
            created=db_event.created,
            last_modified=db_event.last_modified,
            organizer=db_event.organizer,
            attendees=db_event.attendees or [],
            attach=db_event.attach or [],
            classification=db_event.classification,
            priority=db_event.priority,
            rrule=db_event.rrule,
            rdate=db_event.rdate or [],
            exdate=db_event.exdate or [],
            recurrence_id=db_event.recurrence_id,
            tzid=db_event.tzid,
            alarms=db_event.alarms or [],
            raw=db_event.raw,
            title=db_event.title,
            start=db_event.start
        )

    def _is_valid_event(self, event: Event) -> bool:
        """Check if extracted event is valid and substantial."""
        if event is None:
            return False
        
        if event.title is None or event.start is None:
            return False
        
        has_location = event.location is not None
        has_description = event.description is not None and len(event.description) >= 40
        
        return has_location or has_description

    def save_event(self, event: Event, page_id: int, extraction_version: Optional[str] = None) -> int:
        """Save a new event to the database."""
        with self.get_session() as session:
            db_event = self._domain_to_db(event, page_id, extraction_version)
            session.add(db_event)
            session.commit()
            session.refresh(db_event)
            return db_event.event_id

    def upsert_event_by_hash(self, event: Event, page_id: int, extraction_version: Optional[str] = None) -> int:
        """Insert or update event based on content hash to avoid duplicates."""
        content_hash = self._compute_hash(event)
        
        with self.get_session() as session:
            # Check if event with same hash exists for this page
            q = select(DBEvent).where(
                DBEvent.page_id == page_id,
                DBEvent.content_hash == content_hash
            )
            existing = session.execute(q).scalars().first()
            
            if existing:
                # Update existing event
                db_event = self._domain_to_db(event, page_id, extraction_version)
                for key, value in db_event.__dict__.items():
                    if not key.startswith('_') and key not in ['event_id', 'created_at']:
                        setattr(existing, key, value)
                session.commit()
                return existing.event_id
            else:
                # Insert new event
                db_event = self._domain_to_db(event, page_id, extraction_version)
                session.add(db_event)
                session.commit()
                session.refresh(db_event)
                return db_event.event_id

    def get_event_by_id(self, event_id: int) -> Optional[Event]:
        """Get event by ID."""
        with self.get_session() as session:
            q = select(DBEvent).where(DBEvent.event_id == event_id)
            db_event = session.execute(q).scalars().first()
            if not db_event:
                return None
            return self._db_to_domain(db_event)

    def get_events_by_page_id(self, page_id: int) -> List[Event]:
        """Get all events for a specific page."""
        with self.get_session() as session:
            q = select(DBEvent).where(DBEvent.page_id == page_id).order_by(DBEvent.extracted_at.desc())
            db_events = session.execute(q).scalars().all()
            return [self._db_to_domain(e) for e in db_events]

    def get_all_events(self, limit: Optional[int] = None, only_valid: bool = False) -> List[Event]:
        """Get all events from the database."""
        with self.get_session() as session:
            q = select(DBEvent)
            if only_valid:
                q = q.where(DBEvent.is_valid == True)
            q = q.order_by(DBEvent.extracted_at.desc())
            if limit:
                q = q.limit(limit)
            db_events = session.execute(q).scalars().all()
            return [self._db_to_domain(e) for e in db_events]

    def delete_events_by_page_id(self, page_id: int) -> int:
        """Delete all events for a specific page."""
        with self.get_session() as session:
            q = select(DBEvent).where(DBEvent.page_id == page_id)
            events = session.execute(q).scalars().all()
            count = len(events)
            for event in events:
                session.delete(event)
            session.commit()
            return count
