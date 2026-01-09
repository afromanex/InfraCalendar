import json
import logging
from tracemalloc import start
from typing import Dict, List, Optional, Any
from unittest import result

import requests

from app.domain.event import Event
from app.domain.page import Page

logger = logging.getLogger(__name__)


OLLAMA_URL = "http://localhost:11434/api/chat"


class OllamaClient:
    """Simple client for calling a local Ollama chat endpoint.

    It sends a user prompt asking the model to return ONLY JSON with a fixed
    set of keys and attempts to parse the model output as JSON.
    """

    def __init__(self, 
                 url: str = OLLAMA_URL, 
                 model: str = "qwen2.5:1.5b-instruct", 
                 timeout: int = 60):
        self.url = url
        self.model = model
        self.timeout = timeout

    def chat_is_event(self, page: Page) -> bool:

        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                "role": "system",
                "content": (
                    "You are a strict classifier.\n"
                    "Return ONLY true or false.\n"
                    "Answer true ONLY if the text includes at least ONE specific event with a time anchor "
                    "(a date or a day/time like 'Jan 12', 'tomorrow 3pm', 'next Tuesday', etc.).\n"
                    "If the text is a homepage, navigation, general info about a venue/organization, or mentions events "
                    "without a specific date/time, return false.\n"
                    "Do NOT guess dates.\n"
                    "No punctuation. No explanation."
                ),
                },
                {
                    "role": "user",
                    "content": (
                        "Decide if this text contains at least one EVENT INSTANCE with an explicit time anchor.\n"
                        "Time anchor must be present in the text as a DATE or RELATIVE DATE/TIME.\n"
                        "Valid anchors examples: 'Jan 12', 'January 12, 2026', '2026-01-12', 'tomorrow', 'next Tuesday', '3pm', '10:00 AM'.\n"
                        "If you cannot quote an anchor substring from the text, answer false.\n"
                        "Return ONLY true or false.\n\n"
                        f"{page.plain_text[:6000]}"
                    )
                    }
            ],
            "options": {"temperature": 0},
        }


        resp = requests.post(
            self.url,
            json=payload,
            timeout=120,
            )
        
        result = resp.json()["message"]["content"].strip().lower()

        #debugging info
        #print(f"OllamaClient.chat_is_event: {page.page_url}")
        #print(f"resp: {result}")

        is_event = result == "true"

        return is_event

    def chat_page_extract(self, page: Page) -> Event: 
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict information extraction engine. "
                        "Return ONLY valid JSON. No markdown. No extra keys. "
                        "If unknown, use null."
                        ),
                },
                {
                    "role": "user",
                    "content": (
                        "Extract these fields: summary, description, dtstart, dtend, "
                        "duration, location, url, categories, rrule. "
                        f"Text: {page.plain_text}"
                        ),
                },
            ],
            "options": {
                "temperature": 0,
            },
        }
        
        resp = requests.post(
            self.url,
            json=payload,
            timeout=120,
            )
        
        content = resp.json()["message"]["content"].strip()
        #dubugging info
        #print(f"OllamaClient.chat_page_extract: {page.page_url}")
        #print(f"- resp: {content}")
        start = content.find("{")
        end = content.rfind("}")


        if start == -1 or end == -1 or end <= start:
            return None

        data = json.loads(content[start : end + 1])
        
        try:
            event = Event(
                uid=None, 
                dtstamp=None, 

                dtstart=data.get("dtstart"),
                dtend=data.get("dtend"),
                duration=data.get("duration"),

                summary=data.get("summary"),
                description=data.get("description"),
                location=data.get("location"),
                url=page.page_url,
                categories=data.get("categories", []),
                rrule=data.get("rrule"),

                # backward compatibility
                title=data.get("summary"),
                start=data.get("dtstart"),

                raw=content,
            )

            return event 
        except Exception as e:
            logger.error(f"Failed to parse event from Ollama response for page {page.page_url}: {e}")
            return None


__all__ = ["OllamaClient"]
