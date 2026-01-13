import asyncio
import json
import logging
import os

import httpx

from app.domain.event import Event
from app.domain.page import Page

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")

# Global semaphore to limit concurrent Ollama requests
_ollama_semaphore = asyncio.Semaphore(2)  # Max 2 concurrent requests to Ollama

class OllamaClient:
    """Async client for calling a local Ollama chat endpoint.

    It sends a user prompt asking the model to return ONLY JSON with a fixed
    set of keys and attempts to parse the model output as JSON.
    """

    def __init__(self, 
                 url: str = OLLAMA_BASE_URL, 
                 model: str = "qwen2.5:1.5b-instruct", 
                 timeout: int = 120):
        self.url = url
        self.model = model
        self.timeout = timeout
        # Shared async client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5)
        )

    async def chat_page_extract_async(self, page: Page) -> Event:
        from datetime import datetime
        current_year = datetime.now().year
        
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
                        "Do not infer missing dates or times. "
                        f"IMPORTANT: The current year is {current_year}. "
                        f"If a date doesn't specify a year, assume it's {current_year} or {current_year + 1} (whichever makes sense for an upcoming event). "
                        "For dtstart and dtend, include the TIME if mentioned in the text (e.g., '2:00 PM', '14:00'). "
                        "Format date-times as 'YYYY-MM-DD HH:MM' or natural language with time like 'Saturday, February 14, 2026 at 2:00 PM'. "
                        "IMPORTANT: Only include rrule if the text explicitly mentions recurring/repeating events. "
                        "Do NOT add rrule for single one-time events."
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
        
        print(f"DEBUG: OllamaClient.chat_page_extract_async - acquiring semaphore for page_url={page.page_url}")
        async with _ollama_semaphore:
            print(f"DEBUG: OllamaClient.chat_page_extract_async - sending request for page_url={page.page_url}")
            request_url = f"{self.url}/api/chat"
            resp = await self._client.post(
                request_url,
                json=payload,
            )
        print(f"DEBUG: OllamaClient.chat_page_extract_async - received response status_code={resp.status_code} for page_url={page.page_url}")
        
        content = resp.json()["message"]["content"].strip()
        print(f'DEBUG: OllamaClient.chat_page_extract_async - response content for page_url={page.page_url}: {content}')
        #dubugging info
        #print(f"OllamaClient.chat_page_extract: {page.page_url}")
        #print(f"- resp: {content}")
        start = content.find("{")
        end = content.rfind("}")


        if start == -1 or end == -1 or end <= start:
            return None

        data = json.loads(content[start : end + 1])
        
        # Return raw data dict for PageEventExtractor to process
        return data


    async def close(self):
        """Close the HTTP client connection pool."""
        await self._client.aclose()


__all__ = ["OllamaClient"]
