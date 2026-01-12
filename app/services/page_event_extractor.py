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
from app.services.page_date_service import PageDateService

logger = logging.getLogger(__name__)

class PageEventExtractor:
  """Extract a single Event from a `Page` by delegating to NLP and date services.

  Returns an `Event` instance when a sensible start time is found, otherwise `None`.
  """

  def __init__(self, ollama_client: OllamaClient, date_service: PageDateService):
    """Initialize with dependencies.
    
    Args:
      ollama_client: Client for communicating with Ollama
      date_service: Service for date formatting and normalization
    """
    self.client = ollama_client
    self.date_service = date_service

  async def extract_events_async(self, page: Page) -> Event | None:
    try:
      data = await self.client.chat_page_extract_async(page)

      if not data:
        return None
      
      # Format dates and rrule for database compatibility
      dtstart_val = self.date_service.format_date(data.get("dtstart"))
      dtend_val = self.date_service.format_date(data.get("dtend"))
      rrule_val = self.date_service.format_rrule(data.get("rrule"))
      
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
