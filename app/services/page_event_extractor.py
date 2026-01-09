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

  @classmethod
  def extract_events(cls, page: Page) -> Event | None:
    try:
      client = OllamaClient()

      event = client.chat_page_extract(page) 

      return event 
    except Exception as e:
      logger.error(f"Error extracting event from page {page.page_url}: {e}")
      return None

__all__ = ["PageEventExtractor"]
