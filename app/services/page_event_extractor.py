from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Tuple

from dateutil import parser as dtparser
from dateutil.tz import gettz

from app.clients.ollama_client import OllamaClient
from app.domain.event import Event
from app.domain.page import Page

logger = logging.getLogger(__name__)

class PageEventExtractor:
  """Extract a single Event from a `Page` by delegating to NLP and date services.

  Returns an `Event` instance when a sensible start time is found, otherwise `None`.
  """

  @staticmethod
  def format_date(date_obj):
    """Convert dict date to ISO string format."""
    if isinstance(date_obj, dict):
      year = date_obj.get("year")
      month = date_obj.get("month", 1)
      day = date_obj.get("day", 1)
      if year:
        return f"{year:04d}-{month:02d}-{day:02d}"
    return date_obj
  
  @staticmethod
  def format_rrule(rrule_obj):
    """Convert dict rrule to iCalendar RRULE string."""
    if isinstance(rrule_obj, dict):
      parts = []
      if rrule_obj.get("freq"):
        parts.append(f"FREQ={rrule_obj['freq']}")
      if rrule_obj.get("interval"):
        parts.append(f"INTERVAL={rrule_obj['interval']}")
      if rrule_obj.get("count"):
        parts.append(f"COUNT={rrule_obj['count']}")
      return ";".join(parts) if parts else None
    return rrule_obj

  @classmethod
  async def extract_events_async(cls, page: Page) -> Event | None:
    try:
      client = OllamaClient()

      data = await client.chat_page_extract_async(page) 
      await client.close()

      if not data:
        return None
      
      # Format dates and rrule for database compatibility
      dtstart_val = cls.format_date(data.get("dtstart"))
      dtend_val = cls.format_date(data.get("dtend"))
      rrule_val = cls.format_rrule(data.get("rrule"))
      
      # Create Event with formatted data
      event = Event(
        uid=None,
        dtstamp=None,
        dtstart=dtstart_val,
        dtend=dtend_val,
        duration=data.get("duration"),
        summary=data.get("summary"),
        description=data.get("description"),
        location=data.get("location"),
        url=page.page_url,
        categories=data.get("categories", []),
        rrule=rrule_val,
        title=data.get("summary"),
        start=dtstart_val,
        raw=str(data),
      )

      return event 
    except Exception as e:
      print(f"ERROR: Error extracting event from page {page.page_url}: {e}")
      return None

__all__ = ["PageEventExtractor"]
