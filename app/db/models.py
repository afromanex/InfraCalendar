from __future__ import annotations

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey, Boolean, ARRAY, JSON, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class Page(Base):
    __tablename__ = "pages"

    page_id = Column(Integer, primary_key=True)
    page_url = Column(Text, unique=True, nullable=False)
    page_content = Column(Text, nullable=True)
    plain_text = Column(Text, nullable=True)
    http_status = Column(Integer, nullable=True)
    fetched_at = Column(DateTime(timezone=True), nullable=True)
    config_id = Column(Text, nullable=True)  # Config name (e.g., 'starkparks.yml')

    # Relationship to events
    events = relationship("Event", back_populates="page", cascade="all, delete-orphan")


class Event(Base):
    __tablename__ = "events"

    event_id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.page_id", ondelete="CASCADE"), nullable=False)
    
    # iCalendar fields
    uid = Column(Text, nullable=True)
    dtstamp = Column(Text, nullable=True)
    dtstart = Column(Text, nullable=True)
    dtend = Column(Text, nullable=True)
    duration = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    location = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    geo = Column(Text, nullable=True)
    categories = Column(JSON, nullable=True)  # List[str] stored as JSON
    status = Column(Text, nullable=True)
    transp = Column(Text, nullable=True)
    sequence = Column(Integer, nullable=True)
    created = Column(Text, nullable=True)
    last_modified = Column(Text, nullable=True)
    organizer = Column(Text, nullable=True)
    attendees = Column(JSON, nullable=True)  # List[str] stored as JSON
    attach = Column(JSON, nullable=True)  # List[str] stored as JSON
    classification = Column(Text, nullable=True)
    priority = Column(Integer, nullable=True)
    rrule = Column(Text, nullable=True)
    rdate = Column(JSON, nullable=True)  # List[str] stored as JSON
    exdate = Column(JSON, nullable=True)  # List[str] stored as JSON
    recurrence_id = Column(Text, nullable=True)
    tzid = Column(Text, nullable=True)
    alarms = Column(JSON, nullable=True)  # List[Dict[str, Any]] stored as JSON
    
    # Raw and backward-compatible fields
    raw = Column(Text, nullable=True)
    title = Column(Text, nullable=True)
    start = Column(Text, nullable=True)
    
    # Metadata fields
    extracted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    extraction_version = Column(Text, nullable=True)
    is_valid = Column(Boolean, default=False, nullable=False)
    content_hash = Column(Text, nullable=True)  # Hash to detect duplicates
    
    # Relationship to page
    page = relationship("Page", back_populates="events")
