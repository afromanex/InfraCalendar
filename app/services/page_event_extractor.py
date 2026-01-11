from __future__ import annotations

import logging
import traceback
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
  async def extract_events_async(cls, page: Page) -> Event | None:
    try:
      client = OllamaClient()

      event = await client.chat_page_extract_async(page) 
      await client.close()

      return event 
    except Exception as e:
      print(f"ERROR: Error extracting event from page {page.page_url}: {type(e).__name__}: {str(e)}")
      print(f"ERROR: Traceback: {traceback.format_exc()}")
      return None

__all__ = ["PageEventExtractor"]
