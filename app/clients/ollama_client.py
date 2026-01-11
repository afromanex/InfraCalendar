import json
import logging
import os
from tracemalloc import start
from typing import Dict, List, Optional, Any
from unittest import result

import requests

from app.domain.event import Event
from app.domain.page import Page

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://host.docker.internal:11434"

class OllamaClient:
    """Simple client for calling a local Ollama chat endpoint.

    It sends a user prompt asking the model to return ONLY JSON with a fixed
    set of keys and attempts to parse the model output as JSON.
    """

    def __init__(self, 
                 url: str = OLLAMA_BASE_URL, 
                 model: str = "qwen2.5:1.5b-instruct", 
                 timeout: int = 60):
        self.url = url
        self.model = model
        self.timeout = timeout

    def chat_page_extract(self, page: Page) -> Event: 
        payload = {
            "model": self.model,
            "stream": False,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a strict information extraction engine. "
                        "Return ONLY valid JSON. "
                        "Keys must be exactly: summary, description, dtstart, dtend, "
                        "duration, location, url, categories, rrule. "
                        "If a field is not explicitly present in the text, use null. "
                        "Do not infer missing dates or times."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Extract event data from the following text.\n\n"
                        f"{page.plain_text[:4000]}"
                    ),
                },
            ],
            "options": {
                "temperature": 0,
                "num_predict": 350,
                "top_p": 0.1,
            },
        }
        
        print(f"DEBUG: OllamaClient.chat_page_extract - sending request for page_url={page.page_url}")
        request_url = f"{self.url}/api/chat"
        resp = requests.post(
            request_url,
            json=payload,
            timeout=120,
            )
        print(f"DEBUG: OllamaClient.chat_page_extract - received response status_code={resp.status_code} for page_url={page.page_url}")
        
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
            logger.error(f"Failed to parse event from Ollama response for page {page.page_url}: {e} - response content: {content}")
            return None


__all__ = ["OllamaClient"]
