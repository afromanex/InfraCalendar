import json
import requests
from typing import List, Optional

from app.domain.page import Page
from app.services.page_serializers import PageSerializer


class CrawlersClient:
    def __init__(self, base_url: str = "http://localhost:8002", token: Optional[str] = None):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})

    def export(self, config: str, include_html: bool = False, include_plain_text: bool = True, limit: int = 10) -> List[Page]:
        """
        Call the /crawlers/export endpoint with the provided query parameters.

        Example curl equivalent:
        curl -X 'GET' \
          'http://localhost:8002/crawlers/export?config=starkparks.yml&include_html=false&include_plain_text=true&limit=10' \
          -H 'accept: application/json' \
          -H 'Authorization: Bearer secret'

        Returns: requests.Response
        """
        url = f"{self.base_url}/crawlers/export"
        params = {
            "config": config,
            "include_html": str(include_html).lower(),
            "include_plain_text": str(include_plain_text).lower(),
            "limit": str(limit),
        }
        # stream the NDJSON response and parse each JSON line into a Page
        resp = self.session.get(url, params=params, headers={"accept": "application/json"}, stream=True, timeout=60)
        resp.raise_for_status()
        pages: List[Page] = []
        for raw in resp.iter_lines(decode_unicode=True):
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except Exception:
                # skip invalid lines
                continue
            try:
                pages.append(PageSerializer.from_dict(obj))
            except Exception:
                continue
        return pages
